"""Generate the diagrams used in docs/15_frontier/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/frontier/<doc-name>/.

Every number here is quoted in the documents and sourced there. Nothing is
invented for the sake of a shape.

Run with:  pixi run python docs/diagrams/frontier.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'frontier'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
PURPLE: str = '#7b5aa6'
GREY: str = '#9a9a9a'
PALE_BLUE: str = '#e3ecf7'
PALE_RED: str = '#fbe4e8'
PALE_GREY: str = '#eeeeee'


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


def _style(ax, title: str) -> None:
    ax.set_title(title, fontsize=11.5, color=INK, pad=12)
    ax.tick_params(labelsize=9, colors=INK)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)


# --------------------------------------------------------------------------
# overview.md

def evaluation_collapse() -> None:
    """What a benchmark score survives, and what it does not.

    Three independent 2026 results, each a pair: the number as normally
    reported, and the same policy measured a little more carefully.
    """
    fig, (bars, aside) = plt.subplots(1, 2, figsize=(13.2, 5.4),
                                      gridspec_kw={'width_ratios': [1.45, 1]})

    cases = [
        ('LIBERO-PRO\nobjects swapped for\nirrelevant ones', 90.0, 0.0),
        ('LIBERO-Plus\nmild perturbation', 95.0, 30.0),
    ]
    x = np.arange(len(cases))
    width = 0.34

    reported = [c[1] for c in cases]
    actual = [c[2] for c in cases]
    bars.bar(x - width / 2, reported, width, color=BLUE, label='as reported')
    bars.bar(x + width / 2, actual, width, color=RED, label='measured more carefully')

    for xi, (r, a) in enumerate(zip(reported, actual, strict=True)):
        bars.text(xi - width / 2, r + 2, f'{r:.0f}%', ha='center', fontsize=10, color=BLUE)
        bars.text(xi + width / 2, a + 2, f'{a:.0f}%' if a else '0.0%',
                  ha='center', fontsize=10, color=RED)

    bars.set_xticks(x)
    bars.set_xticklabels([c[0] for c in cases], fontsize=9, linespacing=1.5)
    bars.set_ylabel('success rate', fontsize=9.5)
    bars.set_ylim(0, 124)
    bars.legend(fontsize=9, frameon=False, loc='upper center', ncol=2)
    _style(bars, 'The same policies, measured twice')

    # the parameter-count result, which makes the same point differently
    aside.axis('off')
    aside.set_xlim(0, 10)
    aside.set_ylim(0, 10)
    aside.text(0.2, 9.4, 'And the result that settles it', fontsize=11.5, color=INK,
               weight='bold')

    aside.barh([6.9], [95.1], height=0.7, color=GREY, left=0)
    aside.barh([4.9], [97.5], height=0.7, color=BLUE, left=0)
    for y, label, value in ((6.9, '540,000 parameters', 95.1),
                            (4.9, 'a foundation model, 7,700x larger', 97.5)):
        aside.text(0.2, y + 0.6, label, fontsize=9.5, color=INK, va='bottom')
        aside.text(value + 1.5, y, f'{value:.1f}%', fontsize=10, color=INK, va='center')

    aside.text(0.2, 3.4,
               'Two and a half points apart, on a benchmark\n'
               'meant to measure general manipulation.\n\n'
               'Permute the task identifiers and the small one\n'
               'falls to near chance, so the instruction was\n'
               'selecting a task rather than describing one.',
               fontsize=9.5, color=INK, va='top', linespacing=1.7)
    aside.set_xlim(-0.5, 130)
    aside.set_ylim(0, 10)

    fig.text(0.5, -0.04,
             'A benchmark score is a usable regression test and a sanity check that a '
             'pipeline runs. Ranking methods is not among its valid uses.',
             fontsize=10.2, color=INK, ha='center')
    _save(fig, 'overview', 'evaluation-collapse.svg')


def prices_that_moved() -> None:
    """Which arm prices actually fell, from the vendors' own published figures.

    Every point is a price the vendor published, read from a dated page or an
    Internet Archive snapshot. The industrial tier is absent because no major
    vendor publishes a price at all.
    """
    fig, ax = plt.subplots(figsize=(11.6, 5.8))

    rows = [
        ('Trossen ALOHA Stationary kit', 29999.95, 23995.95, GREEN, '-20%, and payload doubled'),
        ('Trossen single arm', 6129.95, 4545.95, GREEN, '-26%'),
        ('UFACTORY xArm 6', 8399.0, 8399.0, RED, 'unchanged over 27 months'),
        ('SO-101 bill of materials', 241.0, 229.88, ORANGE, '-5% in 23 months'),
    ]

    y = np.arange(len(rows))[::-1]
    for yi, (name, before, after, colour, note) in zip(y, rows, strict=True):
        ax.plot([before, after], [yi, yi], color=colour, lw=2.4, zorder=2,
                solid_capstyle='round')
        ax.plot(before, yi, 'o', color=GREY, markersize=9, zorder=3)
        ax.plot(after, yi, 'o', color=colour, markersize=9, zorder=3)
        ax.text(before * 1.06, yi + 0.26, f'${before:,.0f}', fontsize=9, color=MUTED)
        if after != before:
            ax.text(after * 0.94, yi + 0.26, f'${after:,.0f}', fontsize=9,
                    color=colour, ha='right')
        ax.text(38000, yi, note, fontsize=9.5, color=colour, va='center')

    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.set_xscale('log')
    ax.set_xlim(150, 95000)
    ax.set_xlabel('published price, US dollars, log scale', fontsize=9.5)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    _style(ax, 'Which arm prices actually moved, from the vendors\' own published figures')

    fig.text(0.06, -0.10,
             'The industrial tier is missing from this chart because no major '
             'collaborative-arm vendor publishes a price at all: Universal Robots,\n'
             'Franka, Kinova, Doosan, Techman, Elite, JAKA and Dobot all route to '
             'a quote form. So "arms got cheaper" is well evidenced at the\n'
             'cheap end, contradicted in the one mid-range case with public prices, and '
             'simply unknowable in the middle.',
             fontsize=10.2, color=INK, va='top', linespacing=1.8)
    _save(fig, 'overview', 'prices-that-moved.svg')


if __name__ == '__main__':
    evaluation_collapse()
    prices_that_moved()
