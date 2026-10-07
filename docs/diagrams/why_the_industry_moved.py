"""Generate the diagrams for one section of chapter 1 of docs/05_neural-networks/.

    01_what-learning-means/05_why-the-industry-moved.md
        -> images/what-learning-means/why-the-industry-moved/

Run with:  python3 why_the_industry_moved.py
Add --png <folder> to also write PNG copies for checking by eye.

This file is different from every other diagram script in this folder. The
other scripts simulate their own data and then measure it. Nothing here is
simulated and nothing here is measured by this book. Every number below was
copied from a document published outside this project, and the source of each
number is written as a comment immediately above it, with the URL. If a number
has no source comment, it must not be drawn.

Three kinds of number appear, and the comments say which is which:

  CLAIM   a company or a research group reporting on its own system.
  INDEP   a measurement made by somebody who did not build the thing.
  RECORD  a plain published fact, such as a price, a date or a file count.

Numbers that a source showed only in a figure, and never wrote down as text,
are deliberately absent. The pi-0.5 experiment on the number of training
locations is the example: the paper names the six location counts in its text
but gives the scores only in its Figure 8, so this script does not draw them.
"""

import datetime as dt
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'what-learning-means')
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
PURPLE: str = '#6a4fb3'
TEAL: str = '#0f8b8d'
INK: str = '#222222'
MUTED: str = '#777777'

MOVED_DOC: str = 'why-the-industry-moved'


# --------------------------------------------------------------------------
# small helpers, copied from what_learning_means.py so the pictures match
# --------------------------------------------------------------------------

def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _plain(ax: Axes) -> None:
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9.5, colors=INK)


def _day(text: str) -> dt.date:
    return dt.date.fromisoformat(text)


# ==========================================================================
# SECTION 2: when the weights became downloadable
# ==========================================================================

def open_weights_timeline() -> None:
    """One mark for each open release of robot policy weights, by its date."""
    # Every date below is RECORD: the date printed by the publisher itself.
    #
    # Octo, 27M and 93M parameters, arXiv v1 dated 20 May 2024.
    #   https://arxiv.org/abs/2405.12213
    # OpenVLA, 7B parameters, arXiv v1 dated 13 June 2024.
    #   https://arxiv.org/abs/2406.09246
    # pi-0 and pi-0-FAST weights, announced 4 February 2025, Apache-2.0.
    #   https://github.com/Physical-Intelligence/openpi
    # NVIDIA Isaac GR00T N1, press release dated 18 March 2025.
    #   https://investor.nvidia.com/news/press-release-details/2025/
    #   NVIDIA-Announces-Isaac-GR00T-N1--the-Worlds-First-Open-Humanoid-Robot-
    #   Foundation-Model--and-Simulation-Frameworks-to-Speed-Robot-Development/
    # SmolVLA, 450M parameters, Hugging Face blog dated 3 June 2025.
    #   https://huggingface.co/blog/smolvla
    # GO-1, changelog line "[2025/09/19] Our robotic foundation model GO-1
    #   open-sourced." https://github.com/OpenDriveLab/AgiBot-World
    # LeRobot v0.6.0, blog dated 7 July 2026, adds five more open VLAs
    #   (GR00T N1.7, MolmoAct2, EO-1, Multitask DiT, EVO1).
    #   https://huggingface.co/blog/lerobot-release-v060
    events: list[tuple[dt.date, str, str, str]] = [
        (_day('2024-05-20'), 'Octo', '27M and 93M', LINK),
        (_day('2024-06-13'), 'OpenVLA', '7B', PURPLE),
        (_day('2025-02-04'), 'pi-0 and pi-0-FAST', 'Apache-2.0', SLIDE),
        (_day('2025-03-18'), 'GR00T N1', 'NVIDIA', JOINT),
        (_day('2025-06-03'), 'SmolVLA', '450M', TEAL),
        (_day('2025-09-19'), 'GO-1', 'AgiBot World', GRIP),
        (_day('2026-07-07'), 'LeRobot v0.6.0', 'five more', MUTED),
    ]

    fig, ax = plt.subplots(figsize=(10.4, 4.1))
    ax.set_facecolor('white')
    ax.axhline(0.0, color=INK, lw=1.6, zorder=1)

    heights = [0.55, -0.55, 1.00, -0.55, 0.55, -1.00, 0.55]
    for (when, name, note, colour), h in zip(events, heights):
        x = mdates.date2num(when)
        ax.plot([x, x], [0.0, h * 0.78], color=colour, lw=1.5, zorder=2)
        ax.scatter([x], [0.0], s=72, color=colour, zorder=4, edgecolor='white',
                   linewidth=1.1)
        va = 'bottom' if h > 0 else 'top'
        pad = 0.06 if h > 0 else -0.06
        ax.text(x, h * 0.78 + pad, name, ha='center', va=va, fontsize=10.4,
                weight='bold', color=INK)
        ax.text(x, h * 0.78 + pad + (0.20 if h > 0 else -0.20), note,
                ha='center', va=va, fontsize=9.0, color=MUTED)

    ax.set_ylim(-1.80, 1.80)
    ax.set_xlim(mdates.date2num(_day('2024-01-01')),
                mdates.date2num(_day('2026-10-07')))
    ax.set_yticks([])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
    ax.tick_params(labelsize=10.5, colors=INK)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_title('When robot policy weights became free to download',
                 fontsize=12.2, weight='bold', color=INK, pad=14)
    _save(fig, MOVED_DOC, 'open-weights-timeline.svg')

    print('open weights timeline:',
          ', '.join(f'{e[1]} {e[0].isoformat()}' for e in events))


# ==========================================================================
# SECTION 3: how much demonstration data a team can download
# ==========================================================================

def open_datasets_size() -> None:
    """Episode counts of the open demonstration collections, by release date."""
    # RECORD in every case: the count and the release date as the publisher
    # states them.
    #
    # Open X-Embodiment, "over 1 million real robot trajectories", arXiv v1
    #   dated 13 October 2023. https://arxiv.org/abs/2310.08864
    # DROID, "76k trajectories, or 350 hours", arXiv v1 dated 19 March 2024.
    #   https://arxiv.org/abs/2403.12945
    # AgiBot World Alpha, "92,214 trajectories", changelog line
    #   "[2024/12/30] Agibot World Alpha released".
    #   https://github.com/OpenDriveLab/AgiBot-World
    # AgiBot World Beta, "~1,000,000 trajectories", changelog line
    #   "[2025/03/01] AgiBot World Beta".
    #   https://github.com/OpenDriveLab/AgiBot-World
    rows: list[tuple[dt.date, str, int, str]] = [
        (_day('2023-10-13'), 'Open X-Embodiment', 1_000_000, LINK),
        (_day('2024-03-19'), 'DROID', 76_000, PURPLE),
        (_day('2024-12-30'), 'AgiBot World Alpha', 92_214, TEAL),
        (_day('2025-03-01'), 'AgiBot World Beta', 1_003_672, GRIP),
    ]

    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    _plain(ax)
    ax.set_axisbelow(True)
    ax.grid(axis='y', color=GRID, lw=0.8, which='major')

    xs = [mdates.date2num(r[0]) for r in rows]
    ys = [r[2] for r in rows]
    shown = ['more than 1,000,000 episodes', '76,000 episodes',
             '92,214 episodes', '1,003,672 episodes']
    for x, y, (_w, name, _count, colour), text in zip(xs, ys, rows, shown):
        ax.scatter([x], [y], s=150, color=colour, zorder=4, edgecolor='white',
                   linewidth=1.3)
        ax.annotate(f'{name}\n{text}', (x, y),
                    textcoords='offset points', xytext=(0, 20),
                    ha='center', fontsize=9.6, color=INK)

    ax.set_yscale('log')
    ax.set_ylim(3e4, 1.1e7)
    ax.set_xlim(mdates.date2num(_day('2023-04-01')),
                mdates.date2num(_day('2025-12-01')))
    ax.set_ylabel('episodes in the collection (log scale)', fontsize=10.6,
                  color=INK)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_title('How many recorded robot episodes a team can download, '
                 'and when each became available',
                 fontsize=11.8, weight='bold', color=INK, pad=12)
    _save(fig, MOVED_DOC, 'open-datasets-size.svg')

    print('open datasets:',
          ', '.join(f'{r[1]} {r[2]:,} on {r[0].isoformat()}' for r in rows))


# ==========================================================================
# SECTION 4: the memory one open model asks for
# ==========================================================================

def gpu_memory_for_one_model() -> None:
    """The memory the openpi repository says each job needs."""
    # RECORD: the table in the openpi README, read on 7 October 2026.
    #   https://github.com/Physical-Intelligence/openpi
    #   Inference            > 8 GB     example GPU RTX 4090
    #   LoRA fine-tuning     > 22.5 GB  example GPU RTX 4090
    #   Full fine-tuning     > 70 GB    example GPU A100 (80GB) / H100
    jobs: list[tuple[str, float, str, str]] = [
        ('Running the model\non one input', 8.0, 'RTX 4090', SLIDE),
        ('Adapting it with LoRA', 22.5, 'RTX 4090', LINK),
        ('Retraining every\nparameter', 70.0, 'A100 or H100', GRIP),
    ]

    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    _plain(ax)
    ax.set_axisbelow(True)
    ax.grid(axis='y', color=GRID, lw=0.8)

    names = [j[0] for j in jobs]
    vals = [j[1] for j in jobs]
    ax.bar(names, vals, width=0.56, color=[j[3] for j in jobs], alpha=0.85,
           edgecolor=[j[3] for j in jobs], lw=1.3)
    for i, (name, gb, gpu, _c) in enumerate(jobs):
        ax.text(i, gb + 1.6, f'at least {gb:g} GB', ha='center', fontsize=10.4,
                weight='bold', color=INK)
        ax.text(i, gb * 0.5, gpu, ha='center', va='center', fontsize=9.6,
                color='white', weight='bold')

    ax.set_ylim(0, 84)
    ax.set_ylabel('graphics card memory (GB)', fontsize=10.6, color=INK)
    ax.set_title('What the pi-0 authors say each job needs, '
                 'on the card they name for it',
                 fontsize=11.8, weight='bold', color=INK, pad=12)
    _save(fig, MOVED_DOC, 'gpu-memory-for-one-model.svg')

    print('openpi memory:', ', '.join(f'{j[0].replace(chr(10), " ")} {j[1]}GB '
                                      f'({j[2]})' for j in jobs))


# ==========================================================================
# SECTION 6: what an independent suite measured
# ==========================================================================

def success_across_task_variations() -> None:
    """INT-ACT success rates for pi-0 fine-tuned, over the eleven categories."""
    # INDEP: Table 1 of "From Intention to Execution: Probing the
    # Generalization Boundaries of Vision-Language-Action Models",
    # arXiv:2506.09930, row "pi0 finetune". The suite is INT-ACT, 50 tasks.
    #   https://arxiv.org/abs/2506.09930
    rows: list[tuple[str, float]] = [
        ('the original tasks', 30.4),
        ('a new object to pick up', 49.3),
        ('a new place to put it', 24.4),
        ('both of those changed', 21.5),
        ('a new spatial relation', 39.6),
        ('a different action word', 38.5),
        ('an instruction with "not"', 22.2),
        ('the object named by its look', 43.1),
        ('extra objects in the way', 25.2),
        ('a name it has to reason about', 26.4),
        ('that name, plus extra objects', 10.6),
    ]

    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    _plain(ax)
    ax.set_axisbelow(True)
    ax.grid(axis='x', color=GRID, lw=0.8)

    names = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]
    colours = [JOINT if n == 'the original tasks' else LINK for n in names]
    ax.barh(names, vals, height=0.62, color=colours, alpha=0.85,
            edgecolor=colours, lw=1.2)
    for i, v in enumerate(vals):
        ax.text(v + 0.9, i, f'{v:.1f}', va='center', fontsize=9.8, color=INK)

    ax.axvline(30.4, color=JOINT, lw=1.3, ls='--', zorder=1)
    ax.set_xlim(0, 58)
    ax.set_xlabel('tasks completed, out of every 100 attempts', fontsize=10.6,
                  color=INK)
    ax.set_title('One downloadable model, scored by somebody else, '
                 'on eleven kinds of change',
                 fontsize=11.8, weight='bold', color=INK, pad=12)
    _save(fig, MOVED_DOC, 'success-across-task-variations.svg')

    print('INT-ACT pi0-finetune:',
          ', '.join(f'{r[0]} {r[1]}' for r in rows))


# ==========================================================================
# SECTION 7: what went wrong on a real factory floor
# ==========================================================================

def factory_failure_modes() -> None:
    """Share of failed episodes carrying each fault, Siemens packaging study."""
    # RECORD of an INDEP measurement by the deployment team itself: Table I,
    # "Categories of Failures and Their Frequencies for Trials 2 & 3", in
    # "A Factory-Floor Deployment Case Study of VLA Pipelines for Industrial
    # Packaging Task: Workflow, Failures, and Lessons", arXiv:2605.27461.
    # The column used here is the combined "Overall" column. One failed
    # episode can carry more than one fault, so the shares add to more
    # than 100.
    #   https://arxiv.org/abs/2605.27461
    rows: list[tuple[str, float, str]] = [
        ('bag contents left\non the product', 65.0, GRIP),
        ('more than one bag\npicked up at once', 23.0, JOINT),
        ('bag not pushed\nfully into the box', 15.0, LINK),
        ('a poor grasp,\nor no grasp at all', 15.0, PURPLE),
    ]

    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    _plain(ax)
    ax.set_axisbelow(True)
    ax.grid(axis='y', color=GRID, lw=0.8)

    names = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    ax.bar(names, vals, width=0.56, color=[r[2] for r in rows], alpha=0.85,
           edgecolor=[r[2] for r in rows], lw=1.3)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.6, f'{v:.0f}%', ha='center', fontsize=11.0,
                weight='bold', color=INK)

    ax.set_ylim(0, 78)
    ax.set_ylabel('share of the failed attempts', fontsize=10.6, color=INK)
    ax.set_title('What actually went wrong when one open model was fitted '
                 'to one factory job',
                 fontsize=11.8, weight='bold', color=INK, pad=12)
    _save(fig, MOVED_DOC, 'factory-failure-modes.svg')

    print('factory failures:', ', '.join(
        f'{r[0].replace(chr(10), " ")} {r[1]:.0f}%' for r in rows))


# ==========================================================================

def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)

    open_weights_timeline()
    open_datasets_size()
    gpu_memory_for_one_model()
    success_across_task_variations()
    factory_failure_modes()

    print(f'wrote the diagrams under {IMAGES / MOVED_DOC}')


if __name__ == '__main__':
    main()
