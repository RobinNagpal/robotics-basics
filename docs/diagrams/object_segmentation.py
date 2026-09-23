"""Generate the diagrams used in docs/06_object-segmentation/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/object-segmentation/<doc-name>/.

Run with:  pixi run python docs/diagrams/object_segmentation.py
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
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'object-segmentation'

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


if __name__ == '__main__':
    four_answers()
    closed_vs_open()
    what_you_know()
