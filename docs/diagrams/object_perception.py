"""Generate the diagrams used in docs/06_object-perception/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/object-perception/<doc-name>/. All six belong to
01_overview.md, which carries the conceptual framing for the whole area.

The measuring diagrams use the repo's own camera: fx = fy = 277.1 px, cx = 160,
cy = 120, a 320x240 sensor with a 60 degree horizontal field of view. The same
four numbers the camera area uses, so every millimetre can be checked by hand.

Run with:  pixi run python docs/diagrams/object_perception.py
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
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'object-perception'

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


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


def _mug(ax, cx: float, cy: float, scale: float = 1.0, colour: str = BLUE,
         face: str = PALE_BLUE, lw: float = 1.6) -> None:
    """A mug seen from the side: body, handle. Used as the running object."""
    w, h = 13 * scale, 15 * scale
    ax.add_patch(Rectangle((cx - w / 2, cy), w, h, facecolor=face,
                           edgecolor=colour, lw=lw, zorder=3))
    ax.add_patch(Circle((cx + w / 2 + 3.2 * scale, cy + h * 0.55), 3.6 * scale,
                        facecolor='none', edgecolor=colour, lw=lw, zorder=3))


# --------------------------------------------------------------------------
# overview.md
# --------------------------------------------------------------------------

def four_answers() -> None:
    """The four shapes an answer can take, and what each one is worth to a gripper.

    The point of the picture is that these are not four qualities of the same
    answer. They are four different answers, and the one you need is decided by
    what the robot does next, not by which model is most impressive.
    """
    fig, axes = plt.subplots(1, 4, figsize=(15.4, 5.0))

    titles = [
        ('classification', '"there is a mug\nsomewhere in this picture"'),
        ('detection', '"a mug, in this box"'),
        ('segmentation', '"a mug, on these pixels"'),
        ('pose', '"a mug, here, turned this way"'),
    ]
    verdicts = [
        ('cannot reach for it', RED),
        ('enough to reach for a\nsimple object on a table', ORANGE),
        ('enough to grip round it,\nand to miss the handle', GREEN),
        ('enough to put it down\nthe right way up', GREEN),
    ]
    catches = [
        'says nothing about where',
        'the corners of the box\nare table, not mug',
        'still pixels, not millimetres:\nthat is the next document',
        'needs a model of the object,\nor a model that can guess one',
    ]

    for ax, (name, says), (verdict, vcolour), catch in zip(axes, titles, verdicts, catches):
        ax.set_xlim(0, 44)
        ax.set_ylim(-26, 40)
        ax.axis('off')
        ax.add_patch(Rectangle((2, 2), 40, 30, facecolor='white',
                               edgecolor=GREY, lw=1.0, zorder=1))
        _mug(ax, 20, 8, scale=1.05)
        ax.text(22, 36.5, name, fontsize=12.5, color=INK, ha='center', weight='bold')
        ax.text(22, -3.5, says, fontsize=9.6, color=MUTED, ha='center',
                va='top', linespacing=1.6)
        ax.text(22, -11.5, verdict, fontsize=9.6, color=vcolour, ha='center',
                va='top', linespacing=1.6)
        ax.text(22, -20.0, catch, fontsize=8.8, color=MUTED, ha='center',
                va='top', linespacing=1.6, style='italic')

    # classification: a tag over the whole frame
    axes[0].add_patch(Rectangle((2, 2), 40, 30, facecolor=PALE_GREY,
                                edgecolor='none', alpha=0.75, zorder=2))
    axes[0].text(22, 28, 'mug  0.94', fontsize=10.5, color=INK, ha='center', zorder=4)

    # detection: a box round it, including a lot of table
    axes[1].add_patch(Rectangle((11.2, 6.5), 21.5, 18.5, facecolor='none',
                                edgecolor=ORANGE, lw=2.2, zorder=4))
    axes[1].text(11.2, 26.2, 'mug  0.94', fontsize=9.6, color=ORANGE, zorder=4)
    # The two corners that hold no mug at all, marked where they actually are.
    for corner in ((11.2, 6.5), (32.7, 6.5)):
        axes[1].add_patch(Rectangle(corner if corner[0] < 20 else (27.2, 6.5),
                                    5.5, 4.0, facecolor=PALE_ORANGE,
                                    edgecolor='none', alpha=0.9, zorder=2))

    # segmentation: the pixels themselves
    axes[2].add_patch(Rectangle((13.2, 8.0), 13.6, 15.7, facecolor=PALE_GREEN,
                                edgecolor=GREEN, lw=2.2, zorder=4))
    axes[2].add_patch(Circle((29.7, 16.6), 3.9, facecolor='none',
                             edgecolor=GREEN, lw=2.2, zorder=4))

    # pose: axes on the object
    ax = axes[3]
    ax.add_patch(FancyArrowPatch((20, 15), (20, 27), color=PURPLE, lw=2.0,
                                 arrowstyle='-|>', mutation_scale=13, zorder=5))
    ax.add_patch(FancyArrowPatch((20, 15), (31, 12), color=PURPLE, lw=2.0,
                                 arrowstyle='-|>', mutation_scale=13, zorder=5))
    ax.add_patch(FancyArrowPatch((20, 15), (12.5, 10.5), color=PURPLE, lw=2.0,
                                 arrowstyle='-|>', mutation_scale=13, zorder=5))
    ax.text(20.6, 28.2, 'up', fontsize=9.0, color=PURPLE, zorder=5)
    ax.text(31.6, 11.2, 'handle', fontsize=9.0, color=PURPLE, zorder=5)

    fig.text(0.5, -0.085,
             'Each answer is a different question answered. A model that scores well at '
             'the third one tells you nothing about the fourth,\nand most of the work in a '
             'real cell is deciding which of these the next step actually needs.',
             fontsize=10.2, color=INK, ha='center', va='top', linespacing=1.8)
    _save(fig, 'overview', 'four-answers.svg')


def closed_vs_open() -> None:
    """A fixed list of classes against a model you can ask for anything.

    The idea the picture carries is that the difference is not accuracy. It is
    what happens to an object nobody listed, which in a real kitchen or a real
    warehouse is most of them.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.6))

    for ax in axes:
        ax.set_xlim(0, 60)
        ax.set_ylim(-8, 46)
        ax.axis('off')

    # ---------------------------------------------------------------- closed
    ax = axes[0]
    ax.text(30, 44, 'a closed-set model', fontsize=12.5, color=INK,
            ha='center', weight='bold')
    ax.text(30, 40.2, 'trained on a fixed list of classes', fontsize=9.6,
            color=MUTED, ha='center')

    ax.add_patch(FancyBboxPatch((3, 22), 22, 14, boxstyle='round,pad=0.6',
                                facecolor=PALE_BLUE, edgecolor=BLUE, lw=1.3))
    ax.text(14, 33.2, 'it knows exactly', fontsize=9.4, color=BLUE, ha='center')
    ax.text(14, 27.6, 'cup   bottle   bowl\nchair   person   …', fontsize=9.6,
            color=INK, ha='center', va='center', linespacing=1.8)
    ax.text(14, 23.2, '80 of them', fontsize=8.6, color=MUTED, ha='center')

    for label, y, colour, verdict in [
        ('a cup', 15.0, GREEN, 'found'),
        ('a beaker', 8.0, RED, 'silence'),
        ('a wing nut', 1.0, RED, 'silence'),
    ]:
        ax.add_patch(FancyBboxPatch((3, y - 2.4), 22, 5.4,
                                    boxstyle='round,pad=0.35',
                                    facecolor='white', edgecolor=GREY, lw=1.0))
        ax.text(5.2, y + 0.2, label, fontsize=9.6, color=INK, va='center')
        ax.add_patch(FancyArrowPatch((26.5, y + 0.2), (35.5, y + 0.2), color=MUTED,
                                     lw=1.1, arrowstyle='-|>', mutation_scale=11))
        ax.text(37.5, y + 0.2, verdict, fontsize=9.6, color=colour, va='center')

    ax.text(30, -5.6,
            'Anything outside the list does not come back wrong.\nIt does not come back at all.',
            fontsize=9.6, color=INK, ha='center', va='top', linespacing=1.7)

    # ------------------------------------------------------------------ open
    ax = axes[1]
    ax.text(30, 44, 'an open-vocabulary model', fontsize=12.5, color=INK,
            ha='center', weight='bold')
    ax.text(30, 40.2, 'you describe what you want, in words', fontsize=9.6,
            color=MUTED, ha='center')

    ax.add_patch(FancyBboxPatch((3, 24), 22, 11, boxstyle='round,pad=0.6',
                                facecolor=PALE_PURPLE, edgecolor=PURPLE, lw=1.3))
    ax.text(14, 31.6, 'you type', fontsize=9.4, color=PURPLE, ha='center')
    ax.text(14, 27.4, '"the glass beaker"', fontsize=10.2, color=INK, ha='center')

    for label, y, colour, verdict in [
        ('a cup', 15.0, GREEN, 'found'),
        ('a beaker', 8.0, GREEN, 'found'),
        ('a wing nut', 1.0, ORANGE, 'found, if you\nname it well'),
    ]:
        ax.add_patch(FancyBboxPatch((3, y - 2.4), 22, 5.4,
                                    boxstyle='round,pad=0.35',
                                    facecolor='white', edgecolor=GREY, lw=1.0))
        ax.text(5.2, y + 0.2, label, fontsize=9.6, color=INK, va='center')
        ax.add_patch(FancyArrowPatch((26.5, y + 0.2), (35.5, y + 0.2), color=MUTED,
                                     lw=1.1, arrowstyle='-|>', mutation_scale=11))
        ax.text(37.5, y + 0.2, verdict, fontsize=9.6, color=colour, va='center',
                linespacing=1.5)

    ax.text(30, -5.6,
            'The list is gone, and the wording is now part of the system.\n'
            'Two sensible phrasings can give two different answers.',
            fontsize=9.6, color=INK, ha='center', va='top', linespacing=1.7)

    _save(fig, 'overview', 'closed-vs-open.svg')


def what_you_know() -> None:
    """Choosing a family by what you know in advance, not by what is newest.

    Reading it from the left: each question you can answer "yes" to removes work
    later. The techniques on the right are the ones left standing.
    """
    fig, ax = plt.subplots(figsize=(14.6, 7.4))
    ax.set_xlim(0, 152)
    ax.set_ylim(0, 94)
    ax.axis('off')

    rows = [
        (70, 'It is always the same object,\nalways the same way up',
         'a colour range, or template matching', GREEN, PALE_GREEN,
         'milliseconds, no model, no GPU'),
        (53, 'A fixed set of objects you can\ncollect pictures of',
         'fine-tune a detector or a mask model', BLUE, PALE_BLUE,
         'a few hundred labelled pictures'),
        (36, 'Objects you can name but\ncannot collect pictures of',
         'an open-vocabulary model, prompted with text', PURPLE, PALE_PURPLE,
         'no training, but the wording matters'),
        (19, 'Anything at all, and you will\npoint at what you want',
         'a promptable segmenter, given a click or a box', ORANGE, PALE_ORANGE,
         'needs something else to do the pointing'),
        (2, 'Nothing, and the object is\ntransparent or shiny',
         'depth holes, polarisation, or touch', RED, PALE_RED,
         'the camera is the wrong instrument'),
    ]

    ax.text(2, 88, 'What do you know about the object before the robot sees it?',
            fontsize=12.6, color=INK, weight='bold')

    for y, known, answer, colour, pale, cost in rows:
        ax.add_patch(FancyBboxPatch((2, y), 44, 12, boxstyle='round,pad=0.7',
                                    facecolor=pale, edgecolor=colour, lw=1.3))
        ax.text(24, y + 6, known, fontsize=9.8, color=INK, ha='center',
                va='center', linespacing=1.65)

        ax.add_patch(FancyArrowPatch((47.5, y + 6), (56.5, y + 6), color=colour,
                                     lw=1.6, arrowstyle='-|>', mutation_scale=13))

        ax.add_patch(FancyBboxPatch((58, y + 1.2), 52, 9.6,
                                    boxstyle='round,pad=0.7',
                                    facecolor='white', edgecolor=colour, lw=1.3))
        ax.text(84, y + 6, answer, fontsize=10.0, color=colour, ha='center',
                va='center')

        ax.text(113, y + 6, cost, fontsize=9.0, color=MUTED, va='center')

    ax.text(2, -5.5,
            'The rows are in order of how much you know, and the work goes up as you go '
            'down. Nearly every project that struggles here\nhas reached for the bottom row '
            'when it was really in the top two, usually because the bottom row is the one '
            'people write papers about.',
            fontsize=10.2, color=INK, va='top', linespacing=1.8)

    _save(fig, 'overview', 'what-you-know.svg')


FX: float = 277.1          # pixels; the repo's camera


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


# --------------------------------------------------------------------------
# the-wrist-camera.md
# --------------------------------------------------------------------------

REACH_M: float = 0.340           # metres; the camera-to-object distance used throughout
PIXEL_MM: float = REACH_M / FX * 1000.0          # 1.2270 mm, one pixel at 340 mm
RANDOM_MM: float = 2.0 * PIXEL_MM                # 2.4540 mm, one pixel out on each edge
SYSTEMATIC_MM: float = np.tan(np.radians(1.0)) * 340.0   # 5.9347 mm, hand-eye 1 degree


def accuracy_against_views() -> None:
    """What averaging more views buys, and what it cannot touch.

    The random term falls as one over the square root of the number of views.
    The systematic term does not move at all. Their sum in quadrature therefore
    flattens onto a floor that no number of pictures ever crosses, and the right
    panel shows the two things that do cross it.
    """
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(14.6, 6.2),
                                 gridspec_kw={'width_ratios': [1.5, 1.0]})

    n = np.arange(1, 21)
    random = RANDOM_MM / np.sqrt(n)
    total = np.hypot(random, SYSTEMATIC_MM)

    ax.plot(n, total, color=INK, lw=2.4, marker='o', ms=4.5,
            label='total error, the two combined')
    ax.plot(n, np.full_like(n, SYSTEMATIC_MM, dtype=float), color=PURPLE, lw=2.0,
            ls=(0, (6, 3)), label='systematic: hand-eye 1 degree out')
    ax.plot(n, random, color=BLUE, lw=2.0, marker='.', ms=6,
            label='random: mask edge 1 px out each side')

    ax.axhspan(SYSTEMATIC_MM - 0.11, SYSTEMATIC_MM + 0.11, color=PALE_PURPLE,
               alpha=0.95, zorder=0)
    ax.text(2.3, SYSTEMATIC_MM - 0.42,
            'the floor: no number of pictures gets below it',
            fontsize=10.0, color=PURPLE, ha='left', va='top')

    # The two points the reader is being asked to compare.
    for k, colour, dx, ha in ((2, ORANGE, 0.9, 'left'), (20, GREEN, -0.9, 'right')):
        v = float(np.hypot(RANDOM_MM / np.sqrt(k), SYSTEMATIC_MM))
        ax.plot([k], [v], marker='o', ms=10, color=colour, zorder=5)
        ax.text(k + dx, v + 0.5, f'{k} views, {v:.2f} mm', fontsize=10.4,
                color=colour, ha=ha, va='bottom')

    gain = float(np.hypot(RANDOM_MM / np.sqrt(2), SYSTEMATIC_MM)
                 - np.hypot(RANDOM_MM / np.sqrt(20), SYSTEMATIC_MM))
    ax.annotate('', xy=(20.0, np.hypot(RANDOM_MM / np.sqrt(20), SYSTEMATIC_MM) - 0.12),
                xytext=(20.0, 3.5),
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.1))
    ax.text(19.4, 3.3, f'eighteen extra pictures\nbuy {gain:.2f} mm',
            fontsize=10.6, color=INK, ha='right', va='top', linespacing=1.7)

    ax.set_xlabel('pictures averaged, all from about the same place', fontsize=10.4, color=INK)
    ax.set_ylabel('millimetres of error at a 340 mm reach', fontsize=10.4, color=INK)
    ax.set_xticks([1, 2, 5, 10, 15, 20])
    ax.set_xlim(0.4, 21.4)
    ax.set_ylim(0, 8.0)
    ax.tick_params(labelsize=9.4, colors=INK)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)
    ax.legend(fontsize=9.6, loc='center left', bbox_to_anchor=(0.02, 0.56),
              frameon=False)
    ax.set_title('Averaging cuts one of the two terms, and only one',
                 fontsize=12.4, color=INK, pad=12)

    # ------------------------------------------------ what does cross the floor
    options = [
        ('twenty views,\nfrom 340 mm', float(np.hypot(RANDOM_MM / np.sqrt(20), SYSTEMATIC_MM)), GREY),
        ('two views, after\nrecalibrating to 0.25 deg',
         float(np.hypot(RANDOM_MM / np.sqrt(2), np.tan(np.radians(0.25)) * 340.0)), GREEN),
        ('one view, taken\nfrom 150 mm instead',
         float(np.hypot(2.0 * 0.150 / FX * 1000.0, np.tan(np.radians(1.0)) * 150.0)), ORANGE),
    ]
    y = np.arange(len(options))[::-1]
    bx.barh(y, [o[1] for o in options], height=0.46,
            color=[o[2] for o in options], alpha=0.88)
    for yi, (_name, v, _c) in zip(y, options):
        bx.text(v + 0.14, yi, f'{v:.2f} mm', fontsize=10.4, color=INK, va='center')
    bx.axvline(SYSTEMATIC_MM, color=PURPLE, lw=1.6, ls=(0, (5, 3)))
    bx.text(SYSTEMATIC_MM, -0.78, 'the floor from the left panel', fontsize=9.4,
            color=PURPLE, ha='center', va='center')
    bx.set_yticks(y)
    bx.set_yticklabels([o[0] for o in options], fontsize=9.6, color=INK, linespacing=1.6)
    bx.set_xlim(0, 7.6)
    bx.set_ylim(-1.05, 2.5)
    bx.set_xlabel('millimetres of error', fontsize=10.4, color=INK)
    bx.tick_params(labelsize=9.4, colors=INK)
    for side in ('top', 'right'):
        bx.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        bx.spines[side].set_color(GREY)
    bx.set_title('One move beats nineteen', fontsize=12.4, color=INK, pad=12)

    fig.text(0.5, -0.045,
             'Both panels are the repo camera, fx = 277.1 px, at a 340 mm reach. Twenty views land '
             '0.4 per cent above a floor set by the calibration;\nfixing the calibration, or carrying '
             'the camera to 150 mm, moves the floor itself. Moving the camera is the thing the wrist '
             'can do and a fixed camera cannot.',
             fontsize=10.2, color=INK, ha='center', va='top', linespacing=1.8)

    _save(fig, 'the-wrist-camera', 'accuracy-against-views.svg')


def baseline_beats_count() -> None:
    """Where two rays cross decides the depth, and the count does not come into it.

    Ten views packed into 40 mm intersect in a long thin sliver along the line of
    sight. Two views 200 mm apart intersect in a compact patch. The shape of the
    crossing is the whole of triangulation accuracy.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14.4, 7.0))

    exaggeration = 6.0                      # the fans are drawn this much wider than 1 px
    alpha = exaggeration / FX               # radians of half-fan, as drawn
    z = REACH_M * 1000.0                    # 340 mm, object depth

    def lozenge(b_mm: float):
        """Corners of the region where the two outer rays' fans overlap."""
        pts = []
        for sl in (-1, 1):
            for sr in (-1, 1):
                xl, xr = -b_mm / 2.0, b_mm / 2.0
                # each ray leaves its camera aimed at (0, z), tilted by s * alpha
                ml = (0 - xl) / z + sl * alpha * (1 + (xl / z) ** 2)
                mr = (0 - xr) / z + sr * alpha * (1 + (xr / z) ** 2)
                zz = (xr - xl) / (ml - mr)
                pts.append((xl + ml * zz, zz))
        cx = sum(p[0] for p in pts) / 4.0
        cy = sum(p[1] for p in pts) / 4.0
        pts.sort(key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))
        return pts

    panels = [
        (axes[0], 40.0, 10, 'ten views, all inside 40 mm', RED, PALE_RED),
        (axes[1], 200.0, 2, 'two views, 200 mm apart', GREEN, PALE_GREEN),
    ]

    for ax, b_mm, count, title, colour, pale in panels:
        ax.set_xlim(-160, 150)
        ax.set_ylim(-95, 425)
        ax.axis('off')
        ax.invert_yaxis()

        # the camera positions along the arm's sweep
        xs = np.linspace(-b_mm / 2.0, b_mm / 2.0, count)
        for x in xs:
            ax.add_patch(Rectangle((x - 1.7, -13), 3.4, 13, facecolor=PALE_GREY,
                                   edgecolor=INK, lw=0.9, zorder=4))
            ax.plot([x, 0], [0, z], color=GREY, lw=0.6, ls=(0, (4, 4)), zorder=1)

        # the two outer rays, with their fans, stopped short of the caption
        for x in (-b_mm / 2.0, b_mm / 2.0):
            for s_ in (-1, 1):
                m = (0 - x) / z + s_ * alpha * (1 + (x / z) ** 2)
                ax.plot([x, x + m * 412], [0, 412], color=colour, lw=1.2, zorder=2)

        ax.add_patch(Polygon(lozenge(b_mm), closed=True, facecolor=pale,
                             edgecolor=colour, lw=1.8, zorder=3))
        ax.plot([0], [z], marker='o', ms=7, color=INK, zorder=6)

        depth_err = z * z * 1.0 / (FX * b_mm)
        ax.text(-5, -62, title, fontsize=12.2, color=INK, ha='center', weight='bold')
        ax.text(-5, -40, f'the arm moves {b_mm:.0f} mm between the outer two',
                fontsize=9.6, color=MUTED, ha='center')
        ax.text(16, z, 'the object,\n340 mm away', fontsize=9.6, color=INK,
                va='center', linespacing=1.7)
        ax.annotate('', xy=(-11, z), xytext=(-34, z),
                    arrowprops=dict(arrowstyle='-|>', color=colour, lw=1.2))
        ax.text(-96, z + 4,
                f'the two rays cross\nover {depth_err:.1f} mm of depth',
                fontsize=11.0, color=colour, ha='center', va='center', linespacing=1.7)

    fig.text(0.5, 0.965,
             'Two views with a wide baseline beat ten with a narrow one',
             fontsize=13.4, color=INK, ha='center', weight='bold')
    fig.text(0.5, 0.035,
             'The ray fans are drawn six times wider than a one-pixel match error so the shape of the '
             'crossing is visible; the millimetre figures are the true ones\nfor the repo camera, '
             'fx = 277.1 px, and they come from z squared over fx times baseline. Averaging views inside '
             'the 40 mm spread would need twenty-five of them\nto reach what the 200 mm pair reaches '
             'with two, and each one costs a move of the arm.',
             fontsize=10.2, color=INK, ha='center', va='top', linespacing=1.8)

    _save(fig, 'the-wrist-camera', 'baseline-beats-count.svg')


if __name__ == '__main__':
    four_answers()
    closed_vs_open()
    what_you_know()
    no_scale()
    pixels_to_mm()
    error_budget()
    accuracy_against_views()
    baseline_beats_count()
