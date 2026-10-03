"""Generate the diagrams used in docs/07_learned-models/07_language-models/.

Each document's pictures go to a folder named after it, under
docs/images/language-models/. Every picture shows one idea from its own
document: a sentence turning into numbers, a plan picked from a list of skills,
a picture cut into patches, a movement written as eight numbers, and so on.

The scores in the planner picture are example numbers, and the picture says so.
Nothing else here is a measurement.

Run with:  pixi run python ../docs/diagrams/language_models.py
Add --png <folder> to also write PNG copies for checking.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'language-models'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'
PALE: str = '#f3f3f3'
PALE_GREEN: str = '#dff0e2'
PALE_RED: str = '#fbe1e1'

OVERVIEW: str = 'overview'
PLANNERS: str = 'language-models-as-planners'
VLM: str = 'vision-language-models'
VLA: str = 'vision-language-action-models'


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal', family: str = 'sans-serif') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            family=family, zorder=7)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12.5) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 9.5) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=MUTED)


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = PALE,
         edge: str = MUTED, lw: float = 1.0, z: int = 1) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.12',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=z))


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.6, style: str = '-|>') -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0}, zorder=6)


def _table(ax: Axes, x0: float, x1: float, y: float) -> None:
    """A table top seen from the side, with two legs."""
    ax.add_patch(Rectangle((x0, y - 0.12), x1 - x0, 0.12, facecolor='#c8a97e',
                           edgecolor=INK, lw=0.8, zorder=1))
    for lx in (x0 + 0.25, x1 - 0.35):
        ax.add_patch(Rectangle((lx, y - 0.9), 0.1, 0.78, facecolor='#c8a97e',
                               edgecolor=INK, lw=0.8, zorder=1))


def _mug(ax: Axes, x: float, y: float, color: str = GRIP, w: float = 0.5, h: float = 0.6,
         handle: int = 1) -> None:
    """A mug seen from the side, standing with its base centre at (x, y)."""
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=color, edgecolor=INK, lw=0.9,
                           zorder=3))
    hx: float = x + handle * w / 2
    ax.add_patch(Arc((hx, y + h * 0.5), w * 0.55, h * 0.55, theta1=-90 if handle > 0 else 90,
                     theta2=90 if handle > 0 else 270, color=INK, lw=2.4, zorder=2))


def _bowl(ax: Axes, x: float, y: float, w: float = 1.1, h: float = 0.45,
          color: str = LINK_PALE) -> None:
    t = np.linspace(np.pi, 2 * np.pi, 40)
    pts = [(x + w / 2 * np.cos(a), y + h + h * np.sin(a)) for a in t]
    ax.add_patch(Polygon(pts, closed=True, facecolor=color, edgecolor=INK, lw=0.9,
                         zorder=4))


def _apple(ax: Axes, x: float, y: float, r: float = 0.2) -> None:
    ax.add_patch(Circle((x, y + r), r, facecolor=SLIDE, edgecolor=INK, lw=0.8, zorder=3))
    ax.plot([x, x + 0.04], [y + 2 * r, y + 2 * r + 0.1], color=INK, lw=1.4, zorder=3)


def _sponge(ax: Axes, x: float, y: float, w: float = 0.5, h: float = 0.22) -> None:
    ax.add_patch(Rectangle((x - w / 2, y), w, h, facecolor=JOINT, edgecolor=INK, lw=0.8,
                           zorder=3))


def _gripper(ax: Axes, x: float, y: float, size: float = 0.35, opening: float = 0.6,
             color: str = GRIP) -> None:
    """A two-finger gripper pointing down, its finger tips level with y."""
    top: float = y + size * 1.6
    ax.plot([x, x], [top + size * 0.9, top], color=LINK, lw=6, solid_capstyle='butt',
            zorder=5)
    half: float = size * opening
    ax.plot([x - half, x + half], [top, top], color=color, lw=3.5, solid_capstyle='round',
            zorder=5)
    for side in (-1, 1):
        ax.plot([x + side * half, x + side * half], [top, y], color=color, lw=3.5,
                solid_capstyle='round', zorder=5)


def _bubble(ax: Axes, x: float, y: float, w: float, h: float, text: str,
            face: str = 'white', edge: str = MUTED, size: float = 10,
            color: str = INK) -> None:
    _box(ax, x, y, w, h, face=face, edge=edge, z=2)
    _label(ax, x + w / 2, y + h / 2, text, size=size, color=color)


def _panels(n: int, size: tuple[float, float]) -> tuple[Figure, list[Axes]]:
    fig, axes = plt.subplots(1, n, figsize=size, facecolor='white')
    return fig, list(np.atleast_1d(axes))


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# 01_overview.md
# --------------------------------------------------------------------------

def three_ways() -> None:
    """The same table, used three ways: plan in words, answer about it, move in it."""
    fig, axes = _panels(3, (15.5, 5.2))
    for ax in axes:
        _axes(ax, (0, 5), (-0.3, 6.0))

    # 1. planner: words in, a list of steps out
    ax = axes[0]
    _title(ax, 2.5, 5.6, 'A planner')
    _caption(ax, 2.5, 5.15, 'words in, a list of steps out')
    _bubble(ax, 0.3, 4.05, 4.4, 0.65, '"Put the mug in the bowl."', face=LINK_PALE,
            edge=LINK)
    _arrow(ax, (2.5, 3.95), (2.5, 3.45))
    steps = ['1. find the mug', '2. pick up the mug', '3. move over the bowl',
             '4. open the gripper']
    _box(ax, 0.3, 0.9, 4.4, 2.45, face='white')
    for i, s in enumerate(steps):
        _label(ax, 0.6, 2.95 - i * 0.55, s, ha='left', size=10.5)
    _caption(ax, 2.5, 0.35, 'It never sees the table.')
    _caption(ax, 2.5, -0.05, 'It only writes the order of the steps.')

    # 2. vision-language model: picture and question in, answer out
    ax = axes[1]
    _title(ax, 2.5, 5.6, 'A vision-language model')
    _caption(ax, 2.5, 5.15, 'a picture and a question in, an answer out')
    _box(ax, 0.3, 1.6, 4.4, 2.3, face='white', edge=MUTED)
    _table(ax, 0.6, 4.4, 2.35)
    _mug(ax, 1.4, 2.35)
    _bowl(ax, 3.3, 2.35)
    _bubble(ax, 0.3, 4.2, 4.4, 0.6, 'Is the mug in the bowl?', face=LINK_PALE, edge=LINK)
    _bubble(ax, 0.3, 0.55, 4.4, 0.75, 'No. The mug is to the left\nof the bowl.',
            face=PALE_GREEN, edge=SLIDE)
    _caption(ax, 2.5, -0.05, 'It answers in words. It does not move.')

    # 3. vision-language-action model: picture and instruction in, movement out
    ax = axes[2]
    _title(ax, 2.5, 5.6, 'A vision-language-action model')
    _caption(ax, 2.5, 5.15, 'a picture and an instruction in, arm movement out')
    _box(ax, 0.3, 0.55, 4.4, 3.35, face='white', edge=MUTED)
    _table(ax, 0.6, 4.4, 1.3)
    _mug(ax, 1.4, 1.3)
    _bowl(ax, 3.3, 1.3)
    _gripper(ax, 1.4, 1.95, size=0.3, opening=1.1)
    path = [(1.4, 3.05), (1.9, 3.35), (2.5, 3.45), (3.05, 3.3), (3.3, 2.95), (3.3, 2.2)]
    xs, ys = zip(*path)
    ax.plot(xs, ys, color=JOINT, lw=1.6, ls=(0, (3, 2)), zorder=4)
    ax.plot(xs[:-1], ys[:-1], 'o', color=JOINT, ms=5, zorder=6)
    _arrow(ax, path[-2], path[-1], color=JOINT)
    _bubble(ax, 0.3, 4.2, 4.4, 0.6, '"Put the mug in the bowl."', face=LINK_PALE,
            edge=LINK)
    _caption(ax, 2.5, -0.05, 'It outputs the next positions of the gripper.')
    fig.subplots_adjust(wspace=0.08)
    _save(fig, OVERVIEW, 'three-ways-to-use-words.svg')


def words_become_numbers() -> None:
    """A sentence is cut into tokens, and each token becomes a list of numbers."""
    words = ['put', 'the', 'red', 'mug', 'in', 'the', 'sink']
    rng = np.random.default_rng(7)
    table: dict[str, list[float]] = {}
    for w in words:
        if w not in table:
            table[w] = [round(float(v), 1) + 0.0 for v in rng.normal(0, 1, 4)]

    fig, ax = plt.subplots(figsize=(12.5, 6.2), facecolor='white')
    _axes(ax, (-1.4, 14.3), (-1.2, 6.6))
    _title(ax, 7.0, 6.3, 'A sentence becomes numbers before any model reads it')
    _bubble(ax, 3.3, 5.2, 7.4, 0.65, '"put the red mug in the sink"', face=LINK_PALE,
            edge=LINK, size=11.5)
    _label(ax, -1.3, 4.1, '1. cut into\n    tokens', ha='left', size=10, color=MUTED)
    _label(ax, -1.3, 1.4, '2. look up\n    each token\'s\n    numbers', ha='left', size=10,
           color=MUTED)
    x0: float = 2.4
    step: float = 1.68
    cmap = plt.get_cmap('RdBu_r')
    for i, w in enumerate(words):
        cx: float = x0 + i * step
        _arrow(ax, (7.0 + (cx - 7.0) * 0.55, 5.1), (cx, 4.5), lw=1.0)
        same: bool = w == 'the'
        _bubble(ax, cx - 0.62, 3.8, 1.24, 0.6, w, face=PALE_GREEN if same else 'white',
                edge=SLIDE if same else MUTED, size=11)
        _arrow(ax, (cx, 3.7), (cx, 3.1), lw=1.0)
        for k, v in enumerate(table[w]):
            y: float = 2.4 - k * 0.62
            face = cmap(0.5 + max(-1.0, min(1.0, v / 2.5)) * 0.35)
            ax.add_patch(Rectangle((cx - 0.5, y - 0.28), 1.0, 0.56, facecolor=face,
                                   edgecolor=INK, lw=0.6, zorder=3))
            _label(ax, cx, y, f'{v:+.1f}'.replace('-0.0', '+0.0'), size=9.5)
    _caption(ax, 7.0, -0.55, 'Each token becomes the same list of numbers every time. '
             'Both copies of "the" (green) get identical lists.', size=10)
    _caption(ax, 7.0, -0.95, 'A real model uses hundreds or thousands of numbers per token, '
             'not four.', size=10)
    _save(fig, OVERVIEW, 'words-become-numbers.svg')


# --------------------------------------------------------------------------
# 02_language-models-as-planners.md
# --------------------------------------------------------------------------

def spill_to_steps() -> None:
    """The planner can only choose from the skills this robot already has."""
    fig, ax = plt.subplots(figsize=(13.5, 6.4), facecolor='white')
    _axes(ax, (0, 15), (0.0, 7.0))
    _title(ax, 7.5, 6.7, 'The planner picks steps from the skills the robot already has')

    _label(ax, 2.1, 5.9, 'What the person says', size=10.5, color=MUTED)
    _bubble(ax, 0.2, 4.6, 3.8, 1.0, '"I spilled my drink.\nCan you help?"',
            face=LINK_PALE, edge=LINK, size=11.5)

    skills = ['find a sponge', 'pick up the sponge', 'pick up the can', 'go to the table',
              'wipe the table', 'put the sponge in the sink', 'throw the can away',
              'open the drawer']
    _label(ax, 7.2, 5.9, 'The robot\'s skills (fixed list)', size=10.5, color=MUTED)
    _box(ax, 5.3, 0.2, 3.8, 5.4, face=PALE)
    ys: list[float] = [5.1 - i * 0.62 for i in range(len(skills))]
    for s, y in zip(skills, ys):
        _label(ax, 5.55, y, s, ha='left', size=10.5)

    plan = [(1, 'find a sponge', 0), (2, 'pick up the sponge', 1), (3, 'go to the table', 3),
            (4, 'wipe the table', 4), (5, 'put the sponge in the sink', 5)]
    _label(ax, 12.5, 5.9, 'The plan the model writes', size=10.5, color=MUTED)
    _box(ax, 10.3, 1.6, 4.5, 4.0, face='white', edge=SLIDE, lw=1.4)
    for k, (n, s, idx) in enumerate(plan):
        py: float = 5.1 - k * 0.72
        _label(ax, 10.55, py, f'{n}. {s}', ha='left', size=10.5)
        _arrow(ax, (9.2, ys[idx]), (10.25, py), color=SLIDE, lw=1.0)
    _arrow(ax, (4.05, 5.1), (5.2, 5.1), color=MUTED)
    _caption(ax, 12.55, 1.1, 'Three skills are left unused.', size=10)
    _caption(ax, 12.55, 0.7, 'The five were chosen from their names alone.', size=10)
    _caption(ax, 2.1, 3.6, 'The request does not name', size=10)
    _caption(ax, 2.1, 3.2, 'a sponge. The model knows', size=10)
    _caption(ax, 2.1, 2.8, 'that spills need one.', size=10)
    _save(fig, PLANNERS, 'spill-to-steps.svg')


def useful_times_possible() -> None:
    """SayCan's choice at one step: how useful a skill sounds, times whether it can work now."""
    names = ['wipe the table', 'pick up the sponge', 'pick up the apple']
    useful = [0.60, 0.30, 0.10]
    possible = [0.10, 0.90, 0.90]
    both = [u * p for u, p in zip(useful, possible)]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.6), facecolor='white', sharey=True)
    titles = ['Does it help? (language model)', 'Can it work right now?\n(the skill\'s own estimate)',
              'Both multiplied']
    colours = [LINK, JOINT, SLIDE]
    for ax, title, vals, col in zip(axes, titles, [useful, possible, both], colours):
        bars = ax.barh(range(3), vals, color=col, height=0.55, zorder=2)
        ax.set_xlim(0, 1.15)
        ax.set_title(title, fontsize=11, color=INK, pad=10)
        ax.invert_yaxis()
        ax.tick_params(labelsize=10, colors=INK, length=0)
        ax.set_xticks([0, 0.5, 1.0])
        ax.grid(axis='x', color=GRID, lw=0.8, zorder=0)
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color(MUTED)
        for b, v in zip(bars, vals):
            ax.text(v + 0.03, b.get_y() + b.get_height() / 2, f'{v:.2f}', va='center',
                    fontsize=10, color=INK)
    axes[0].set_yticks(range(3))
    axes[0].set_yticklabels(names, fontsize=11)
    axes[2].patches[1].set_edgecolor(INK)
    axes[2].patches[1].set_linewidth(1.6)
    axes[2].text(0.47, 1.0, 'chosen', va='center', fontsize=10.5, color=SLIDE,
                 weight='bold')
    fig.suptitle('Request: "I spilled my drink." The robot is holding nothing.  '
                 '(Example numbers.)', fontsize=11.5, color=INK, y=1.04)
    fig.subplots_adjust(wspace=0.12)
    _save(fig, PLANNERS, 'useful-times-possible.svg')


def code_then_motion() -> None:
    """The model writes a short program; ordinary functions carry it out."""
    fig, ax = plt.subplots(figsize=(14.0, 5.6), facecolor='white')
    _axes(ax, (0, 16), (-0.8, 6.2))
    _title(ax, 8.0, 5.9, 'The model writes a short program. The robot\'s own functions run it.')

    _bubble(ax, 0.1, 3.2, 3.6, 1.3, '"Stack the blocks:\nblue at the bottom,\nthen red, then green."',
            face=LINK_PALE, edge=LINK, size=10.5)
    _arrow(ax, (3.8, 3.85), (4.6, 3.85))

    code = ['blue  = find("blue block")',
            'red   = find("red block")',
            'green = find("green block")',
            '',
            'pick_and_place(red,   on=blue)',
            'pick_and_place(green, on=red)']
    _box(ax, 4.7, 1.3, 5.9, 4.0, face='#fbfbf5', edge=MUTED)
    for i, line in enumerate(code):
        _label(ax, 4.95, 4.8 - i * 0.62, line, ha='left', size=10.5, family='monospace')
    _caption(ax, 7.65, 0.85, 'written by the language model', size=10)
    _caption(ax, 7.65, 0.45, '(find and pick_and_place are written by people)', size=10)
    _arrow(ax, (10.7, 3.3), (11.5, 3.3))

    _table(ax, 11.8, 15.8, 1.2)
    s: float = 0.75
    for k, col in enumerate([LINK, GRIP, SLIDE]):
        ax.add_patch(Rectangle((13.8 - s / 2, 1.2 + k * s), s, s, facecolor=col,
                               edgecolor=INK, lw=0.9, zorder=3))
    _gripper(ax, 13.8, 1.2 + 3 * s + 0.05, size=0.32, opening=1.3)
    _caption(ax, 13.8, -0.35, 'the result on the table', size=10)
    _save(fig, PLANNERS, 'code-then-motion.svg')


# --------------------------------------------------------------------------
# 03_vision-language-models.md
# --------------------------------------------------------------------------

def _scene(ax: Axes, x0: float, y0: float, w: float = 5.0, h: float = 3.2,
           apple_in_bowl: bool = True) -> None:
    """A camera picture of a table: two mugs, a bowl, an apple."""
    ax.add_patch(Rectangle((x0, y0), w, h, facecolor='#fafafa', edgecolor=INK, lw=1.2,
                           zorder=0))
    ty: float = y0 + 1.0
    _table(ax, x0 + 0.25, x0 + w - 0.25, ty)
    _mug(ax, x0 + 0.9, ty, color=GRIP)
    _mug(ax, x0 + 2.4, ty, color=LINK)
    if apple_in_bowl:
        _apple(ax, x0 + 3.85, ty + 0.3, r=0.17)
    _bowl(ax, x0 + 3.85, ty, w=1.1)


def asking_about_a_picture() -> None:
    """One picture, three questions, three answers, one of them a point on the picture."""
    fig, ax = plt.subplots(figsize=(13.0, 5.6), facecolor='white')
    _axes(ax, (0, 14.5), (0.5, 6.2))
    _title(ax, 7.25, 5.9, 'One camera picture, three questions')
    _scene(ax, 0.2, 1.4, w=5.2, h=3.6)
    handle = (0.2 + 0.9 + 0.25 + 0.14, 1.4 + 1.0 + 0.3)
    ax.plot([handle[0]], [handle[1]], 'o', ms=13, mfc='none', mec=JOINT, mew=2.5, zorder=8)
    ax.plot([handle[0]], [handle[1]], '+', ms=10, color=JOINT, mew=2, zorder=8)
    _label(ax, handle[0] + 0.3, handle[1] + 1.05, 'the answer\nto question 3', size=9.5,
           color=WRIST)
    _arrow(ax, (handle[0] + 0.2, handle[1] + 0.75), (handle[0] + 0.02, handle[1] + 0.25),
           color=WRIST, lw=1.2)
    _caption(ax, 2.8, 1.05, 'the camera picture', size=10)

    qa = [('What is on the table?', 'Two mugs, a bowl and an apple.', 'words'),
          ('Is there anything in the bowl?', 'Yes, an apple.', 'words'),
          ('Point to the handle of the red mug.', 'x = 112, y = 305 (in pixels)', 'a point')]
    for i, (q, a, kind) in enumerate(qa):
        y: float = 4.4 - i * 1.55
        _bubble(ax, 6.2, y, 4.0, 0.62, q, face=LINK_PALE, edge=LINK, size=10)
        _arrow(ax, (10.25, y + 0.31), (10.7, y + 0.31), lw=1.2)
        _bubble(ax, 10.75, y, 3.6, 0.62, a, face=PALE_GREEN, edge=SLIDE, size=10)
        _caption(ax, 12.55, y - 0.25, f'answer: {kind}', size=9)
    _save(fig, VLM, 'asking-about-a-picture.svg')


def patches_and_words() -> None:
    """The picture is cut into patches; patches and words go in as one row of tokens."""
    fig, ax = plt.subplots(figsize=(15.0, 6.0), facecolor='white')
    _axes(ax, (0, 19.6), (-1.0, 6.9))
    _title(ax, 9.8, 6.6, 'The picture becomes tokens too, and joins the words in one row')

    x0, y0, w, h = 0.3, 2.3, 4.0, 3.2
    _scene(ax, x0, y0, w=w, h=h)
    n: int = 4
    for k in range(1, n):
        ax.plot([x0 + k * w / n] * 2, [y0, y0 + h], color=WRIST, lw=1.6, zorder=9)
        ax.plot([x0, x0 + w], [y0 + k * h / n] * 2, color=WRIST, lw=1.6, zorder=9)
    _caption(ax, x0 + w / 2, y0 - 0.35, 'cut into 4 x 4 = 16 patches', size=10)

    # one row of tokens: 16 picture tokens, then 7 word tokens
    ry: float = 0.6
    sz: float = 0.42
    gap: float = 0.08
    for k in range(16):
        cx: float = 0.3 + k * (sz + gap)
        ax.add_patch(Rectangle((cx, ry), sz, sz, facecolor='#f6d3b8', edgecolor=WRIST,
                               lw=1.0, zorder=3))
    _caption(ax, 0.3 + 8 * (sz + gap), ry - 0.4, '16 picture tokens, one per patch', size=10)
    _arrow(ax, (x0 + w / 2, y0 - 0.6), (x0 + w / 2, ry + sz + 0.12))
    words = ['Is', 'the', 'mug', 'in', 'the', 'bowl', '?']
    wx: float = 0.3 + 16 * (sz + gap) + 0.2
    for k, wd in enumerate(words):
        bx: float = wx + k * 0.78
        _bubble(ax, bx, ry - 0.05, 0.7, sz + 0.1, wd, face=LINK_PALE, edge=LINK, size=10)
    _caption(ax, wx + 3.5 * 0.78, ry - 0.4, '7 word tokens', size=10)
    _bubble(ax, wx + 0.35, 3.6, 4.8, 0.62, '"Is the mug in the bowl?"', face=LINK_PALE,
            edge=LINK, size=10.5)
    _arrow(ax, (wx + 2.75, 3.5), (wx + 2.75, ry + sz + 0.15))
    end: float = wx + 7 * 0.78 - 0.08

    # into the model
    mx0: float = end + 0.7
    _box(ax, mx0, -0.35, 2.6, 2.3, face='white', edge=INK, lw=1.2)
    cols = [mx0 + 0.45 + c * 0.57 for c in range(4)]
    rows = [1.55, 0.8, 0.05]
    for r in range(2):
        for c1 in cols:
            for c2 in cols:
                ax.plot([c1, c2], [rows[r], rows[r + 1]], color=GRID, lw=0.5, zorder=2)
    for ry2 in rows:
        for cx2 in cols:
            ax.add_patch(Circle((cx2, ry2), 0.14, facecolor=LINK_PALE, edgecolor=LINK, lw=0.8,
                                zorder=3))
    _caption(ax, mx0 + 1.3, 2.25, 'language model', size=10)
    _arrow(ax, (end + 0.05, ry + sz / 2), (mx0 - 0.05, ry + sz / 2))
    _arrow(ax, (mx0 + 2.65, ry + sz / 2), (mx0 + 3.15, ry + sz / 2))
    _bubble(ax, mx0 + 3.2, ry - 0.1, 0.8, sz + 0.2, 'No', face=PALE_GREEN, edge=SLIDE,
            size=11)
    _save(fig, VLM, 'patches-and-words.svg')


def checking_success() -> None:
    """Ask the same yes/no question after every step, and stop when the answer is yes."""
    frames = [(1.0, 0.0, True), (1.0, 1.1, True), (2.5, 1.7, True), (3.85, 0.45, False)]
    answers = ['No', 'No', 'No', 'Yes']
    labels = ['before', 'mug lifted', 'moving', 'released']
    fig, axes = _panels(4, (14.0, 4.6))
    for i, (ax, (mx, lift, held), ans, lab) in enumerate(zip(axes, frames, answers, labels)):
        _axes(ax, (-0.1, 5.1), (-1.5, 4.5))
        ax.add_patch(Rectangle((0, 0), 5.0, 3.6, facecolor='#fafafa', edgecolor=INK, lw=1.0))
        ty: float = 0.9
        _table(ax, 0.2, 4.8, ty)
        _bowl(ax, 3.85, ty, w=1.2, h=0.5)
        my: float = ty + lift
        _mug(ax, mx, my, w=0.45, h=0.5)
        if held:
            if i == 0:
                _gripper(ax, mx, my + 0.9, size=0.28, opening=1.1)
            else:
                _gripper(ax, mx, my + 0.15, size=0.28, opening=0.95)
        else:
            _gripper(ax, mx, my + 1.1, size=0.28, opening=1.1)
        _label(ax, 2.5, 4.1, f'step {i + 1}: {lab}', size=10.5)
        good: bool = ans == 'Yes'
        _bubble(ax, 1.4, -1.25, 2.2, 0.7, ans, face=PALE_GREEN if good else PALE_RED,
                edge=SLIDE if good else GRIP, size=12)
        _arrow(ax, (2.5, -0.15), (2.5, -0.5), lw=1.2)
    fig.suptitle('After each step the robot asks: "Is the red mug in the bowl?"',
                 fontsize=12.5, color=INK, weight='bold', y=0.93)
    fig.subplots_adjust(wspace=0.06)
    _save(fig, VLM, 'checking-success.svg')


# --------------------------------------------------------------------------
# 04_vision-language-action-models.md
# --------------------------------------------------------------------------

def actions_as_words() -> None:
    """RT-2's trick: each part of a movement is one of 256 steps, written as a number."""
    tokens = ['1', '128', '91', '241', '5', '101', '127', '217']
    parts = ['stop?', 'x', 'y', 'z', 'roll', 'pitch', 'yaw', 'grip']
    fig, ax = plt.subplots(figsize=(13.0, 6.2), facecolor='white')
    _axes(ax, (0, 14), (-0.6, 6.8))
    _title(ax, 7.0, 6.5, 'A movement written as eight numbers, so a language model can say it')

    # top: the range of one part (x) cut into 256 steps
    x0, x1, ly = 1.0, 13.0, 4.9
    ax.plot([x0, x1], [ly, ly], color=INK, lw=1.4)
    for k in range(0, 257, 16):
        tx: float = x0 + (x1 - x0) * k / 256
        ax.plot([tx, tx], [ly - 0.12, ly + 0.12], color=INK, lw=0.9)
    for k in range(0, 256, 4):
        tx = x0 + (x1 - x0) * k / 256
        ax.plot([tx, tx], [ly - 0.05, ly + 0.05], color=MUTED, lw=0.5)
    _label(ax, x0, ly - 0.45, '0', size=10)
    _label(ax, x1, ly - 0.45, '255', size=10)
    _label(ax, x0, ly + 0.5, 'largest move\nto the left', size=9.5, color=MUTED)
    _label(ax, x1, ly + 0.5, 'largest move\nto the right', size=9.5, color=MUTED)
    mid: float = x0 + (x1 - x0) * 128.5 / 256
    ax.add_patch(Rectangle((x0 + (x1 - x0) * 128 / 256, ly - 0.2), (x1 - x0) / 256 * 1.0,
                           0.4, facecolor=JOINT, edgecolor=JOINT, zorder=4))
    _label(ax, mid, ly + 0.5, 'step 128:\nabout no move', size=9.5, color=WRIST)
    _label(ax, mid, ly - 0.5, 'the x in the string below', size=9.5, color=WRIST)
    _caption(ax, 7.0, 3.75, 'One part of the movement, x, cut into 256 equal steps. '
             'The model only has to name the step.', size=10)

    # bottom: the eight numbers
    bw: float = 1.3
    bx0: float = 7.0 - 4 * (bw + 0.15) + 0.075
    for k, (t, p) in enumerate(zip(tokens, parts)):
        bx: float = bx0 + k * (bw + 0.15)
        hl: bool = p == 'x'
        _bubble(ax, bx, 1.9, bw, 0.8, t, face='#fdebc8' if hl else LINK_PALE,
                edge=WRIST if hl else LINK, size=13)
        _label(ax, bx + bw / 2, 1.45, p, size=10.5, color=MUTED)
    _caption(ax, 7.0, 0.75, 'stop? = is the task finished;  x, y, z = how far to move the '
             'gripper;', size=10)
    _caption(ax, 7.0, 0.35, 'roll, pitch, yaw = how far to turn it;  grip = how far to '
             'open the fingers', size=10)
    _caption(ax, 7.0, -0.3, 'The example string is the one printed on the RT-2 project page.',
             size=9.5)
    _save(fig, VLA, 'actions-as-words.svg')


def backbone_and_expert() -> None:
    """A small action expert turns random numbers into a smooth path, step by step."""
    rng = np.random.default_rng(3)
    t = np.linspace(0, 1, 10)
    goal_x = 0.4 + 2.6 * t
    goal_y = 2.6 - 1.9 * t ** 2 + 0.6 * np.sin(np.pi * t)
    noise_x = rng.uniform(0.2, 3.2, 10)
    noise_y = rng.uniform(0.4, 3.0, 10)
    noise_x[0], noise_y[0] = goal_x[0], goal_y[0]     # the gripper's position now is known

    fig, axes = plt.subplots(1, 4, figsize=(15.0, 4.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1, 1, 1]})
    ax = axes[0]
    _axes(ax, (0, 4.4), (-0.9, 3.9))
    _scene_small(ax)
    _bubble(ax, 0.2, -0.75, 4.0, 0.55, '"put the mug in the bowl"', face=LINK_PALE,
            edge=LINK, size=10)
    _label(ax, 2.2, 3.65, 'What goes in', size=11)

    stages = [(0.0, 'start: 10 random points'), (0.6, 'after a few steps'),
              (1.0, 'finished: a chunk of 10\ngripper positions')]
    for ax, (a, title) in zip(axes[1:], stages):
        _axes(ax, (0, 3.6), (0, 3.4))
        ax.add_patch(Rectangle((0.05, 0.05), 3.5, 3.3, facecolor='#fafafa', edgecolor=GRID,
                               lw=1.0))
        px = (1 - a) * noise_x + a * goal_x
        py = (1 - a) * noise_y + a * goal_y
        if a == 1.0:
            ax.plot(px, py, color=JOINT, lw=1.4, zorder=3)
        ax.plot(px, py, 'o', color=JOINT, mec=INK, mew=0.6, ms=8, zorder=4)
        ax.plot([px[0]], [py[0]], 'o', color=LINK, mec=INK, ms=9, zorder=5)
        ax.set_title(title, fontsize=11, color=INK, pad=6)
    _label(axes[3], goal_x[0], goal_y[0] + 0.35, 'now', size=9.5, color=LINK)
    _label(axes[3], goal_x[-1] + 0.1, goal_y[-1] - 0.35, 'over the bowl', size=9.5,
           color=MUTED)
    fig.text(0.5, 0.08, 'The vision-language model reads the picture and the words once. '
             'The small action expert then nudges the points towards a sensible path, a few '
             'times over.', ha='center', fontsize=10, color=MUTED, wrap=True)
    fig.subplots_adjust(wspace=0.12)
    _save(fig, VLA, 'backbone-and-action-expert.svg')


def _scene_small(ax: Axes) -> None:
    ax.add_patch(Rectangle((0.2, 0.0), 4.0, 3.2, facecolor='#fafafa', edgecolor=INK, lw=1.0))
    _table(ax, 0.4, 4.0, 1.0)
    _mug(ax, 1.2, 1.0, w=0.45, h=0.55)
    _bowl(ax, 3.1, 1.0, w=1.1, h=0.45)
    _gripper(ax, 1.2, 1.9, size=0.28, opening=1.1)


def one_step_vs_chunk() -> None:
    """One model call per command, against one model call per chunk of commands."""
    fig, axes = plt.subplots(2, 1, figsize=(13.0, 5.4), facecolor='white')
    total: float = 12.0
    rows = [('One action per model call', 1.0, 1), ('A chunk of 8 actions per model call',
                                                    1.0, 8)]
    for ax, (title, call, per) in zip(axes, rows):
        _axes(ax, (-2.3, total + 0.3), (-0.9, 2.1))
        ax.set_aspect('auto')
        ax.plot([0, total], [0, 0], color=MUTED, lw=1.0)
        _label(ax, -1.2, 1.25, 'model\nthinking', size=9.5, color=MUTED)
        _label(ax, -1.2, 0.35, 'command\nto the arm', size=9.5, color=MUTED)
        ax.text(total / 2, 1.95, title, fontsize=11.5, ha='center', color=INK, weight='bold')
        t: float = 0.0
        sent: int = 0
        while t + call <= total + 1e-9:
            ax.add_patch(Rectangle((t, 1.0), call - 0.06, 0.5, facecolor=LINK_PALE,
                                   edgecolor=LINK, lw=0.9))
            if per == 1:
                ax.plot([t + call, t + call], [0, 0.6], color=JOINT, lw=2.4)
                sent += 1
            else:
                for k in range(per):
                    cx: float = t + call + k * (call / per) * 1.0
                    if cx <= total:
                        ax.plot([cx, cx], [0, 0.6], color=JOINT, lw=2.4)
                        sent += 1
            t += call if per == 1 else call
        note: str = 'with a pause before each' if per == 1 else 'with no pauses'
        _label(ax, total / 2, -0.55, f'{sent} commands, {note}', size=10, color=INK)
    axes[1].set_ylim(-0.9, 2.1)
    fig.text(0.5, 0.0, 'Blue boxes: one run of the model.  Orange lines: one command sent '
             'to the arm.  The chunk keeps the arm busy while the next chunk is worked out.',
             ha='center', fontsize=10, color=MUTED)
    fig.subplots_adjust(hspace=0.35)
    _save(fig, VLA, 'one-step-vs-chunk.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    three_ways()
    words_become_numbers()
    spill_to_steps()
    useful_times_possible()
    code_then_motion()
    asking_about_a_picture()
    patches_and_words()
    checking_success()
    actions_as_words()
    backbone_and_expert()
    one_step_vs_chunk()


if __name__ == '__main__':
    main()
