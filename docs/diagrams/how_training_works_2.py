"""Generate the diagrams for the last two pages of docs/06_neural-networks/03_how-training-works/.

    03_backpropagation.md   -> images/how-training-works/backpropagation/
    04_the-training-loop.md -> images/how-training-works/the-training-loop/

Run with:  python3 docs/diagrams/how_training_works_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints each one so the two documents can quote the same values.

What is real and what is made up. The tiny two-input network of
03_backpropagation.md is worked out exactly, forward and backward, and its nine
gradients are checked against a finite-difference measurement in the same
script. The deep stacks used for the vanishing and exploding gradient pictures
are real forward and backward passes written out in NumPy, on random weights
drawn with a seeded numpy.random.default_rng, and the residual, normalisation
and clipping comparisons rerun those same stacks with one thing changed. The
training runs of 04_the-training-loop.md are real: a two-layer network with a
rectified linear unit in the middle, trained by hand-written stochastic
gradient descent, momentum, Adam and AdamW on simulated data. The data itself
is simulated, because the point of the pictures is the shape of the loss curve
rather than any particular task: the inputs are drawn from a seeded generator
and the targets come from a fixed smooth formula plus noise. The step timings
in the last section are measured on the machine that runs the script, so they
differ from machine to machine, and the page says so.
"""

import pathlib
import sys
import time

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'how-training-works'
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
PURPLE: str = '#6a4fb3'
TEAL: str = '#0f8b8d'
INK: str = '#222222'
MUTED: str = '#777777'

BP_DOC: str = 'backpropagation'
TL_DOC: str = 'the-training-loop'

Arr = NDArray[np.float64]


# --------------------------------------------------------------------------
# small helpers, copied from the conventions of what_models_are_3.py
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
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(labelsize=9.5, colors=INK)


def _plot_style(ax: Axes) -> None:
    _plain(ax)
    ax.grid(True, color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def _blank(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_facecolor('white')
    ax.axis('off')


def _box(ax: Axes, x: float, y: float, w: float, h: float, face: str = LINK_PALE,
         edge: str = LINK, lw: float = 1.4) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.10',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=3))


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float],
           colour: str = INK, lw: float = 1.5, style: str = '-|>',
           shrink: float = 2.0) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, color=colour, lw=lw,
                                 mutation_scale=13, shrinkA=shrink, shrinkB=shrink,
                                 zorder=2))


def _node(ax: Axes, x: float, y: float, r: float, label: str, value: str,
          face: str = LINK_PALE, edge: str = LINK) -> None:
    ax.add_patch(plt.Circle((x, y), r, facecolor=face, edgecolor=edge, lw=1.6, zorder=4))
    ax.text(x, y + 0.10, label, ha='center', va='center', fontsize=10.5,
            color=INK, zorder=5)
    ax.text(x, y - 0.14, value, ha='center', va='center', fontsize=10.5,
            weight='bold', color=INK, zorder=5)


# ==========================================================================
# PAGE 3, SECTION 1: the chain rule through two stages
#
# A winch with two stages. Turning the handle one turn turns the drum
# GEAR turns, and every drum turn lifts the hook LIFT centimetres.
# ==========================================================================

GEAR: float = 3.0        # drum turns per handle turn
LIFT: float = 2.5        # centimetres lifted per drum turn
NUDGE: float = 0.2       # handle turns in the worked nudge


def chain_two_stages() -> None:
    """Stage one times stage two: the two slopes multiply."""
    both = GEAR * LIFT
    drum_nudge = GEAR * NUDGE
    lift_nudge = LIFT * drum_nudge
    print(f'[chain] one handle turn -> {GEAR:.0f} drum turns -> {both:.1f} cm')
    print(f'[chain] a nudge of {NUDGE} handle turns -> {drum_nudge:.1f} drum turns '
          f'-> {lift_nudge:.2f} cm')

    fig, ax = plt.subplots(figsize=(10.6, 3.9), facecolor='white')
    _blank(ax, (0, 10.6), (0, 3.9))

    _box(ax, 0.2, 1.5, 2.3, 1.2, face='#f3f3f3', edge=MUTED)
    ax.text(1.35, 2.32, 'handle', ha='center', fontsize=11.5, color=INK)
    ax.text(1.35, 1.85, '1 turn', ha='center', fontsize=13, weight='bold', color=INK)

    _box(ax, 4.1, 1.5, 2.3, 1.2, face=LINK_PALE, edge=LINK)
    ax.text(5.25, 2.32, 'drum', ha='center', fontsize=11.5, color=INK)
    ax.text(5.25, 1.85, f'{GEAR:.0f} turns', ha='center', fontsize=13, weight='bold', color=INK)

    _box(ax, 8.0, 1.5, 2.3, 1.2, face='#d9efdc', edge=SLIDE)
    ax.text(9.15, 2.32, 'hook', ha='center', fontsize=11.5, color=INK)
    ax.text(9.15, 1.85, f'{both:.1f} cm up', ha='center', fontsize=13, weight='bold', color=INK)

    _arrow(ax, (2.6, 2.1), (4.0, 2.1), colour=INK, lw=2.0)
    ax.text(3.3, 2.45, f'x {GEAR:.0f}', ha='center', fontsize=12, weight='bold', color=LINK)
    ax.text(3.3, 1.70, 'drum turns\nper handle turn', ha='center', fontsize=9, color=MUTED)

    _arrow(ax, (6.5, 2.1), (7.9, 2.1), colour=INK, lw=2.0)
    ax.text(7.2, 2.45, f'x {LIFT}', ha='center', fontsize=12, weight='bold', color=SLIDE)
    ax.text(7.2, 1.70, 'cm per\ndrum turn', ha='center', fontsize=9, color=MUTED)

    _arrow(ax, (1.35, 0.95), (9.15, 0.95), colour=GRIP, lw=2.0)
    ax.text(5.25, 0.55, f'the whole winch: {GEAR:.0f} x {LIFT} = {both:.1f} cm '
                        f'per handle turn', ha='center', fontsize=11.5, color=GRIP,
            weight='bold')

    ax.text(5.3, 3.5, 'Two stages in a row: multiply the two slopes to get the slope of the whole thing',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    _save(fig, BP_DOC, 'chain-two-stages.svg')


def _stage_one(a: Arr) -> Arr:
    """Drum turns from handle turns: a straight line of slope GEAR."""
    return GEAR * a


def _stage_two(g: Arr) -> Arr:
    """Centimetres lifted from drum turns, when the rope winds on a spool.

    Each new coil sits on top of the last, so the spool grows as it fills and
    a late turn lifts more than an early one. Lift = 0.4 * g^2 centimetres.
    """
    return 0.4 * g ** 2


def chain_curved_stages() -> None:
    """The same two stages when the second one bends, so the slope depends on where you are."""
    a0 = 2.0
    g0 = float(_stage_one(np.array([a0]))[0])
    lift0 = float(_stage_two(np.array([g0]))[0])
    slope1 = GEAR
    slope2 = 0.8 * g0
    whole = slope1 * slope2
    a1 = 1.0
    g1 = float(_stage_one(np.array([a1]))[0])
    whole1 = GEAR * 0.8 * g1
    print(f'[curved] at {a0} handle turns: drum {g0:.0f} turns, hook {lift0:.1f} cm')
    print(f'[curved] slopes {slope1:.0f} and {slope2:.1f} multiply to {whole:.1f} cm '
          f'per handle turn')
    print(f'[curved] at {a1} handle turn the same product is {GEAR:.0f} x {0.8 * g1:.1f} '
          f'= {whole1:.1f} cm per handle turn')

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    a = np.linspace(0, 3.2, 200)
    g = _stage_one(a)
    ax = axes[0]
    _plot_style(ax)
    ax.plot(a, g, color=LINK, lw=2.4)
    ax.plot([a0], [g0], 'o', color=GRIP, ms=8, zorder=5)
    ax.plot([0, a0, a0], [g0, g0, 0], color=GRIP, lw=1.0, ls=':')
    ax.set_xlabel('handle turns', fontsize=10)
    ax.set_ylabel('drum turns', fontsize=10)
    ax.set_title(f'Stage one is straight: slope {slope1:.0f} drum turns per handle turn',
                 fontsize=11.5, weight='bold')
    ax.text(0.35, 8.2, f'at {a0:.0f} handle turns\nthe drum is at {g0:.0f} turns',
            fontsize=10, color=INK)

    ax = axes[1]
    _plot_style(ax)
    gg = np.linspace(0, 9.6, 300)
    ax.plot(gg, _stage_two(gg), color=SLIDE, lw=2.4)
    ax.plot([g0], [lift0], 'o', color=GRIP, ms=8, zorder=5)
    tan = lift0 + slope2 * (gg - g0)
    keep = (gg > g0 - 2.6) & (gg < g0 + 2.6)
    ax.plot(gg[keep], tan[keep], color=GRIP, lw=1.8, ls='--')
    ax.plot([g1], [_stage_two(np.array([g1]))[0]], 'o', color=PURPLE, ms=8, zorder=5)
    tan1 = _stage_two(np.array([g1]))[0] + 0.8 * g1 * (gg - g1)
    keep1 = (gg > g1 - 1.6) & (gg < g1 + 1.6)
    ax.plot(gg[keep1], tan1[keep1], color=PURPLE, lw=1.8, ls='--')
    ax.set_xlabel('drum turns', fontsize=10)
    ax.set_ylabel('centimetres lifted', fontsize=10)
    ax.set_title(f'Stage two bends: its slope at {g0:.0f} turns is {slope2:.1f} cm per turn',
                 fontsize=11.5, weight='bold')
    ax.annotate(f'slope {slope2:.1f}', xy=(g0 + 1.6, lift0 + slope2 * 1.6),
                xytext=(g0 - 3.4, lift0 + 9.0), fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='-', color=GRIP, lw=1.0))
    ax.annotate(f'slope {0.8 * g1:.1f}', xy=(g1 + 1.1, _stage_two(np.array([g1]))[0] + 0.8 * g1 * 1.1),
                xytext=(g1 + 0.4, 16.0), fontsize=10, color=PURPLE,
                arrowprops=dict(arrowstyle='-', color=PURPLE, lw=1.0))
    fig.suptitle(f'Where you are matters: the whole winch lifts {whole:.1f} cm per handle turn '
                 f'at {a0:.0f} turns, {whole1:.1f} cm at {a1:.0f}',
                 fontsize=12.5, weight='bold', y=1.02)
    fig.tight_layout()
    _save(fig, BP_DOC, 'chain-curved-stages.svg')


def chain_finite_difference() -> None:
    """Measure the whole winch by nudging it, and watch the measurement meet the product of slopes."""
    a0 = 2.0
    exact = GEAR * 0.8 * (GEAR * a0)
    steps = np.array([1.0, 0.5, 0.2, 0.05, 0.01, 0.001])
    measured = np.array([
        float((_stage_two(_stage_one(np.array([a0 + s])))[0] -
               _stage_two(_stage_one(np.array([a0])))[0]) / s)
        for s in steps])
    for s, m in zip(steps, measured):
        print(f'[nudge] nudge {s:<6} -> measured {m:7.3f} cm per handle turn '
              f'(exact {exact:.1f})')

    fig, ax = plt.subplots(figsize=(10.0, 4.6), facecolor='white')
    _plot_style(ax)
    xs = np.arange(len(steps))
    ax.bar(xs, measured, color=LINK_PALE, edgecolor=LINK, lw=1.4, width=0.6)
    ax.axhline(exact, color=GRIP, lw=2.0, ls='--')
    ax.text(len(steps) - 0.45, exact + 0.55,
            f'the two slopes multiplied: {GEAR:.0f} x {0.8 * GEAR * a0:.1f} = {exact:.1f}',
            ha='right', fontsize=10.5, color=GRIP, weight='bold')
    for x, m in zip(xs, measured):
        ax.text(x, m + 0.2, f'{m:.3f}', ha='center', fontsize=10, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{s:g}' for s in steps])
    ax.set_ylim(0, max(measured) * 1.18)
    ax.set_xlabel('size of the nudge, in handle turns', fontsize=10)
    ax.set_ylabel('measured cm lifted per handle turn', fontsize=10)
    ax.set_title('Smaller nudges measure the same slope the chain rule works out without measuring',
                 fontsize=12, weight='bold')
    _save(fig, BP_DOC, 'chain-finite-difference.svg')


# ==========================================================================
# PAGE 3, SECTIONS 2 and 3: the tiny network, forward and backward
# ==========================================================================

X1: float = 1.0
X2: float = 0.5
TARGET: float = 2.0
W11: float = 0.8      # x1 -> hidden 1
W21: float = -0.4     # x2 -> hidden 1
B1: float = 0.1
W12: float = -0.6     # x1 -> hidden 2
W22: float = 0.2      # x2 -> hidden 2
B2: float = -0.1
V1: float = 1.2       # hidden 1 -> output
V2: float = -0.5      # hidden 2 -> output
C: float = 0.3
LR: float = 0.1

NAMES: list[str] = ['w11', 'w21', 'b1', 'w12', 'w22', 'b2', 'v1', 'v2', 'c']


def tiny_forward(p: dict[str, float], x1: float = X1, x2: float = X2,
                 target: float = TARGET) -> dict[str, float]:
    """Forward pass of the tiny network, every step kept so the page can quote it."""
    z1 = x1 * p['w11'] + x2 * p['w21'] + p['b1']
    z2 = x1 * p['w12'] + x2 * p['w22'] + p['b2']
    h1 = max(z1, 0.0)
    h2 = max(z2, 0.0)
    u = h1 * p['v1'] + h2 * p['v2'] + p['c']
    err = u - target
    return {'z1': z1, 'z2': z2, 'h1': h1, 'h2': h2, 'u': u, 'err': err,
            'loss': err ** 2}


def tiny_backward(p: dict[str, float], f: dict[str, float],
                  x1: float = X1, x2: float = X2) -> dict[str, float]:
    """Backward pass of the tiny network, worked out by the chain rule."""
    du = 2.0 * f['err']
    dv1, dv2, dc = du * f['h1'], du * f['h2'], du
    dh1, dh2 = du * p['v1'], du * p['v2']
    dz1 = dh1 * (1.0 if f['z1'] > 0 else 0.0)
    dz2 = dh2 * (1.0 if f['z2'] > 0 else 0.0)
    return {'du': du, 'dv1': dv1, 'dv2': dv2, 'dc': dc, 'dh1': dh1, 'dh2': dh2,
            'dz1': dz1, 'dz2': dz2,
            'dw11': dz1 * x1, 'dw21': dz1 * x2, 'db1': dz1,
            'dw12': dz2 * x1, 'dw22': dz2 * x2, 'db2': dz2}


PARAMS: dict[str, float] = {'w11': W11, 'w21': W21, 'b1': B1, 'w12': W12,
                            'w22': W22, 'b2': B2, 'v1': V1, 'v2': V2, 'c': C}
FWD: dict[str, float] = tiny_forward(PARAMS)
BWD: dict[str, float] = tiny_backward(PARAMS, FWD)


def tiny_network_forward() -> None:
    """The network drawn with its weights on the lines and its values in the nodes."""
    f = FWD
    print(f'[forward] z1 = {X1}x{W11} + {X2}x{W21} + {B1} = {f["z1"]:.2f}, h1 = {f["h1"]:.2f}')
    print(f'[forward] z2 = {X1}x{W12} + {X2}x{W22} + {B2} = {f["z2"]:.2f}, h2 = {f["h2"]:.2f}')
    print(f'[forward] u  = {f["h1"]:.2f}x{V1} + {f["h2"]:.2f}x{V2} + {C} = {f["u"]:.2f}')
    print(f'[forward] target {TARGET}, error {f["err"]:.2f}, loss {f["loss"]:.4f}')

    fig, ax = plt.subplots(figsize=(11.0, 5.0), facecolor='white')
    _blank(ax, (0, 11.0), (0, 5.0))
    r = 0.46
    xs, hs, us = 1.0, 4.3, 7.6
    y_top, y_bot, y_mid = 3.5, 1.3, 2.4
    _node(ax, xs, y_top, r, 'x1', f'{X1:.1f}', face='#f3f3f3', edge=MUTED)
    _node(ax, xs, y_bot, r, 'x2', f'{X2:.1f}', face='#f3f3f3', edge=MUTED)
    _node(ax, hs, y_top, r, 'h1', f'{f["h1"]:.2f}')
    _node(ax, hs, y_bot, r, 'h2', f'{f["h2"]:.2f}')
    _node(ax, us, y_mid, r, 'u', f'{f["u"]:.2f}', face='#d9efdc', edge=SLIDE)

    def edge(p0: tuple[float, float], p1: tuple[float, float], text: str,
             t: float, colour: str) -> None:
        _arrow(ax, p0, p1, colour=MUTED, lw=1.4)
        mx = p0[0] + t * (p1[0] - p0[0])
        my = p0[1] + t * (p1[1] - p0[1])
        ax.text(mx, my + 0.20, text, ha='center', fontsize=10.5, color=colour,
                weight='bold', zorder=6,
                bbox=dict(boxstyle='round,pad=0.12', facecolor='white', edgecolor='none'))

    edge((xs + r, y_top), (hs - r, y_top), f'w11 = {W11}', 0.5, LINK)
    edge((xs + r, y_bot), (hs - r, y_bot), f'w22 = {W22}', 0.5, LINK)
    edge((xs + r, y_top), (hs - r, y_bot), f'w12 = {W12}', 0.70, LINK)
    edge((xs + r, y_bot), (hs - r, y_top), f'w21 = {W21}', 0.70, LINK)
    edge((hs + r, y_top), (us - r, y_mid), f'v1 = {V1}', 0.45, SLIDE)
    edge((hs + r, y_bot), (us - r, y_mid), f'v2 = {V2}', 0.45, SLIDE)

    ax.text(hs, y_top + r + 0.42, f'bias b1 = {B1}', ha='center', fontsize=9.5, color=MUTED)
    ax.text(hs, y_bot - r - 0.48, f'bias b2 = {B2}', ha='center', fontsize=9.5, color=MUTED)
    ax.text(us, y_mid + r + 0.42, f'bias c = {C}', ha='center', fontsize=9.5, color=MUTED)
    ax.text(hs, y_top + 0.98, f'z1 = {f["z1"]:.2f}, above 0', ha='center', fontsize=9.5,
            color=LINK)
    ax.text(hs, y_bot - 1.0, f'z2 = {f["z2"]:.2f}, below 0, so h2 = 0', ha='center',
            fontsize=9.5, color=GRIP)

    _box(ax, 8.9, 1.9, 1.9, 1.0, face='#fde3e3', edge=GRIP)
    ax.text(9.85, 2.63, 'loss', ha='center', fontsize=10.5, color=INK)
    ax.text(9.85, 2.22, f'{f["loss"]:.4f}', ha='center', fontsize=12, weight='bold', color=INK)
    _arrow(ax, (us + r, y_mid), (8.85, y_mid), colour=MUTED, lw=1.4)
    ax.text(8.5, 1.55, f'target {TARGET:.1f}', ha='center', fontsize=9.5, color=MUTED)

    ax.text(5.5, 4.6, f'The forward pass: two inputs become {f["u"]:.2f}, '
                      f'and the target is {TARGET:.1f}',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    _save(fig, BP_DOC, 'tiny-network-forward.svg')


def forward_arithmetic() -> None:
    """Every multiplication of the forward pass, written out as the page writes it."""
    f = FWD
    lines = [
        ('hidden neuron 1', [
            f'x1 x w11   =  {X1:>5.2f} x {W11:>5.2f}  =  {X1 * W11:>6.2f}',
            f'x2 x w21   =  {X2:>5.2f} x {W21:>5.2f}  =  {X2 * W21:>6.2f}',
            f'bias b1                      =  {B1:>6.2f}',
            f'                        z1   =  {f["z1"]:>6.2f}',
            f'            above 0, so h1   =  {f["h1"]:>6.2f}',
        ]),
        ('hidden neuron 2', [
            f'x1 x w12   =  {X1:>5.2f} x {W12:>5.2f}  =  {X1 * W12:>6.2f}',
            f'x2 x w22   =  {X2:>5.2f} x {W22:>5.2f}  =  {X2 * W22:>6.2f}',
            f'bias b2                      =  {B2:>6.2f}',
            f'                        z2   =  {f["z2"]:>6.2f}',
            f'            below 0, so h2   =  {f["h2"]:>6.2f}',
        ]),
        ('the output, and the loss', [
            f'h1 x v1    =  {f["h1"]:>5.2f} x {V1:>5.2f}  =  {f["h1"] * V1:>6.2f}',
            f'h2 x v2    =  {f["h2"]:>5.2f} x {V2:>5.2f}  =  {f["h2"] * V2:>6.2f}',
            f'bias c                       =  {C:>6.2f}',
            f'                        u    =  {f["u"]:>6.2f}',
            f'u - target =  {f["u"]:>5.2f} - {TARGET:>5.2f}  =  {f["err"]:>6.2f}',
            f'loss = (u - target) squared  =  {f["loss"]:>6.4f}',
        ]),
    ]
    fig, ax = plt.subplots(figsize=(10.4, 6.6), facecolor='white')
    _blank(ax, (0, 10.4), (0, 6.6))
    y = 5.55
    for title, rows in lines:
        ax.text(0.35, y, title, fontsize=11.5, weight='bold', color=LINK)
        y -= 0.34
        for row in rows:
            ax.text(0.55, y, row, fontsize=11, family='monospace', color=INK)
            y -= 0.30
        y -= 0.22
    ax.text(5.2, 6.25, 'The whole forward pass is nine multiplications and six additions',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    _save(fig, BP_DOC, 'forward-arithmetic.svg')


def loss_at_this_prediction() -> None:
    """The loss as a curve against the prediction, with this prediction marked on it."""
    f = FWD
    preds = np.linspace(-0.5, 4.5, 400)
    loss = (preds - TARGET) ** 2
    slope = 2.0 * f['err']
    print(f'[loss curve] at u = {f["u"]:.2f} the loss is {f["loss"]:.4f} '
          f'and its slope is {slope:.2f}')
    fig, ax = plt.subplots(figsize=(9.6, 4.8), facecolor='white')
    _plot_style(ax)
    ax.plot(preds, loss, color=LINK, lw=2.4)
    ax.plot([f['u']], [f['loss']], 'o', color=GRIP, ms=9, zorder=5)
    tan = f['loss'] + slope * (preds - f['u'])
    keep = (preds > f['u'] - 1.0) & (preds < f['u'] + 1.0)
    ax.plot(preds[keep], tan[keep], color=GRIP, lw=1.8, ls='--')
    ax.axvline(TARGET, color=SLIDE, lw=1.6, ls=':')
    ax.text(TARGET + 0.08, 3.6, f'target {TARGET:.1f}', fontsize=10, color=SLIDE)
    ax.annotate(f'u = {f["u"]:.2f}, loss = {f["loss"]:.4f}\nslope {slope:.2f}: '
                f'raising u lowers the loss',
                xy=(f['u'], f['loss']), xytext=(f['u'] - 1.35, 2.6), fontsize=10.5,
                color=INK, arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.2))
    ax.set_xlabel('what the network says, u', fontsize=10)
    ax.set_ylabel('loss', fontsize=10)
    ax.set_title('The first slope of the backward pass: how the loss changes when the output changes',
                 fontsize=12, weight='bold')
    _save(fig, BP_DOC, 'loss-at-this-prediction.svg')


def tiny_network_backward() -> None:
    """The same network with the blame travelling backwards along every line."""
    f, b = FWD, BWD
    print(f'[backward] dloss/du = 2 x {f["err"]:.2f} = {b["du"]:.2f}')
    print(f'[backward] dv1 = {b["du"]:.2f} x {f["h1"]:.2f} = {b["dv1"]:.3f}, '
          f'dv2 = {b["du"]:.2f} x {f["h2"]:.2f} = {b["dv2"]:.3f}, dc = {b["dc"]:.2f}')
    print(f'[backward] dh1 = {b["du"]:.2f} x {V1} = {b["dh1"]:.3f}, '
          f'dh2 = {b["du"]:.2f} x {V2} = {b["dh2"]:.3f}')
    print(f'[backward] dz1 = {b["dz1"]:.3f} (gate open), dz2 = {b["dz2"]:.3f} (gate shut)')
    print(f'[backward] dw11 = {b["dw11"]:.3f}, dw21 = {b["dw21"]:.3f}, db1 = {b["db1"]:.3f}')
    print(f'[backward] dw12 = {b["dw12"]:.3f}, dw22 = {b["dw22"]:.3f}, db2 = {b["db2"]:.3f}')

    fig, ax = plt.subplots(figsize=(11.2, 5.4), facecolor='white')
    _blank(ax, (0, 11.2), (0, 5.4))
    r = 0.46
    xs, hs, us = 1.0, 4.3, 7.6
    y_top, y_bot, y_mid = 3.7, 1.4, 2.55
    _node(ax, xs, y_top, r, 'x1', f'{X1:.1f}', face='#f3f3f3', edge=MUTED)
    _node(ax, xs, y_bot, r, 'x2', f'{X2:.1f}', face='#f3f3f3', edge=MUTED)
    _node(ax, hs, y_top, r, 'h1', f'{f["h1"]:.2f}')
    _node(ax, hs, y_bot, r, 'h2', f'{f["h2"]:.2f}')
    _node(ax, us, y_mid, r, 'u', f'{f["u"]:.2f}', face='#d9efdc', edge=SLIDE)

    def back_edge(p0: tuple[float, float], p1: tuple[float, float], text: str,
                  t: float) -> None:
        _arrow(ax, p1, p0, colour=GRIP, lw=1.5)
        mx = p1[0] + t * (p0[0] - p1[0])
        my = p1[1] + t * (p0[1] - p1[1])
        ax.text(mx, my - 0.26, text, ha='center', fontsize=10, color=GRIP,
                weight='bold', zorder=6,
                bbox=dict(boxstyle='round,pad=0.12', facecolor='white', edgecolor='none'))

    back_edge((xs + r, y_top), (hs - r, y_top), f'dw11 = {b["dw11"]:.3f}', 0.5)
    back_edge((xs + r, y_bot), (hs - r, y_bot), f'dw22 = {b["dw22"]:.3f}', 0.5)
    back_edge((xs + r, y_top), (hs - r, y_bot), f'dw12 = {b["dw12"]:.3f}', 0.72)
    back_edge((xs + r, y_bot), (hs - r, y_top), f'dw21 = {b["dw21"]:.3f}', 0.72)
    back_edge((hs + r, y_top), (us - r, y_mid), f'dv1 = {b["dv1"]:.3f}', 0.48)
    back_edge((hs + r, y_bot), (us - r, y_mid), f'dv2 = {b["dv2"]:.3f}', 0.48)
    _arrow(ax, (8.85, y_mid), (us + r, y_mid), colour=GRIP, lw=1.8)

    _box(ax, 8.9, 2.05, 2.1, 1.0, face='#fde3e3', edge=GRIP)
    ax.text(9.95, 2.78, 'loss', ha='center', fontsize=10.5, color=INK)
    ax.text(9.95, 2.36, f'{f["loss"]:.4f}', ha='center', fontsize=12, weight='bold', color=INK)
    ax.text(8.45, 3.15, f'dloss/du\n= {b["du"]:.2f}', ha='center', fontsize=10,
            color=GRIP, weight='bold')

    ax.text(hs, y_top + r + 0.40, f'dloss/dh1 = {b["dh1"]:.3f},  so dloss/dz1 = {b["dz1"]:.3f}',
            ha='center', fontsize=9.5, color=LINK)
    ax.text(hs, y_bot - r - 0.52, f'dloss/dh2 = {b["dh2"]:.2f}, but the gate is shut, '
                                  f'so dloss/dz2 = {b["dz2"]:.2f}',
            ha='center', fontsize=9.5, color=GRIP)
    ax.text(hs, y_top + 0.96, f'db1 = {b["db1"]:.3f}', ha='center', fontsize=9.5, color=MUTED)
    ax.text(us, y_mid - r - 0.44, f'dc = {b["dc"]:.2f}', ha='center', fontsize=9.5, color=MUTED)

    ax.text(5.6, 5.0, 'The backward pass: the blame starts at the loss and is handed back '
                      'along every line',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    _save(fig, BP_DOC, 'tiny-network-backward.svg')


def blame_bars() -> None:
    """All nine gradients side by side, so the reader can see which weight is blamed most."""
    b = BWD
    grads = [b['dw11'], b['dw21'], b['db1'], b['dw12'], b['dw22'], b['db2'],
             b['dv1'], b['dv2'], b['dc']]
    print('[blame] ' + ', '.join(f'{n}:{g:+.3f}' for n, g in zip(NAMES, grads)))
    biggest = NAMES[int(np.argmax(np.abs(grads)))]
    print(f'[blame] the biggest share of the blame belongs to {biggest}')

    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plot_style(ax)
    colours = [GRIP if g < 0 else LINK for g in grads]
    ax.bar(np.arange(9), grads, color=colours, edgecolor=INK, lw=0.8, width=0.6)
    for i, g in enumerate(grads):
        off = -0.14 if g < 0 else 0.07
        ax.text(i, g + off, f'{g:+.3f}', ha='center', fontsize=10, color=INK)
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xticks(np.arange(9))
    ax.set_xticklabels(NAMES, fontsize=10.5)
    ax.set_ylim(-2.45, 0.55)
    ax.set_ylabel('how much the loss grows when the weight grows by 1', fontsize=10)
    ax.set_title(f'The nine shares of the blame: three of them are exactly 0 because '
                 f'hidden neuron 2 gave {FWD["h2"]:.0f}',
                 fontsize=12, weight='bold')
    _save(fig, BP_DOC, 'blame-bars.svg')


def relu_gate() -> None:
    """The rectified linear unit as a gate that is either open with slope 1 or shut with slope 0."""
    f, b = FWD, BWD
    z = np.linspace(-1.6, 1.6, 400)
    h = np.maximum(z, 0.0)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    ax.plot(z, h, color=LINK, lw=2.6)
    ax.plot([f['z1']], [f['h1']], 'o', color=SLIDE, ms=9, zorder=5)
    ax.plot([f['z2']], [f['h2']], 'o', color=GRIP, ms=9, zorder=5)
    ax.annotate(f'z1 = {f["z1"]:.2f}\nslope 1, gate open', xy=(f['z1'], f['h1']),
                xytext=(f['z1'] - 1.5, 1.05), fontsize=10, color=SLIDE,
                arrowprops=dict(arrowstyle='-|>', color=SLIDE, lw=1.2))
    ax.annotate(f'z2 = {f["z2"]:.2f}\nslope 0, gate shut', xy=(f['z2'], f['h2']),
                xytext=(f['z2'] - 0.95, 0.72), fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.2))
    ax.set_xlabel('the weighted sum, z', fontsize=10)
    ax.set_ylabel('the neuron output, h', fontsize=10)
    ax.set_title('The rectified linear unit has only two slopes', fontsize=11.5, weight='bold')

    ax = axes[1]
    _plot_style(ax)
    rows = ['dloss/dh', 'slope of the gate', 'dloss/dz']
    n1 = [b['dh1'], 1.0, b['dz1']]
    n2 = [b['dh2'], 0.0, b['dz2']]
    ys = np.arange(3)
    ax.barh(ys + 0.18, n1, height=0.32, color=LINK_PALE, edgecolor=LINK, lw=1.3,
            label='hidden neuron 1')
    ax.barh(ys - 0.18, n2, height=0.32, color='#fde3e3', edgecolor=GRIP, lw=1.3,
            label='hidden neuron 2')
    for y, v in zip(ys + 0.18, n1):
        ax.text(v + (0.07 if v >= 0 else -0.07), y, f'{v:+.3f}', fontsize=10,
                va='center', ha='left' if v >= 0 else 'right', color=INK)
    for y, v in zip(ys - 0.18, n2):
        ax.text(v + (0.07 if v >= 0 else -0.07), y, f'{v:+.3f}', fontsize=10,
                va='center', ha='left' if v >= 0 else 'right', color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels(rows, fontsize=10.5)
    ax.axvline(0, color=INK, lw=1.0)
    ax.set_xlim(-2.9, 1.5)
    ax.set_xlabel('value in the backward pass', fontsize=10)
    ax.set_title('Multiplying by the gate slope stops the blame at neuron 2',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    fig.tight_layout()
    _save(fig, BP_DOC, 'relu-gate.svg')


def one_step() -> None:
    """One step of gradient descent on the tiny network: the weights move, the loss falls."""
    after = {k: PARAMS[k] - LR * BWD['d' + k] for k in NAMES}
    f2 = tiny_forward(after)
    print(f'[step] learning rate {LR}')
    for k in NAMES:
        print(f'[step] {k}: {PARAMS[k]:+.4f} - {LR} x {BWD["d" + k]:+.4f} = {after[k]:+.4f}')
    print(f'[step] the output moved from {FWD["u"]:.2f} to {f2["u"]:.4f}, '
          f'and the loss from {FWD["loss"]:.4f} to {f2["loss"]:.4f}')
    drop = 100.0 * (1.0 - f2['loss'] / FWD['loss'])
    print(f'[step] that is a fall of {drop:.1f} per cent of the loss in one step')

    losses = [FWD['loss']]
    p = dict(PARAMS)
    for _ in range(12):
        f = tiny_forward(p)
        g = tiny_backward(p, f)
        p = {k: p[k] - LR * g['d' + k] for k in NAMES}
        losses.append(tiny_forward(p)['loss'])
    print('[step] twelve more steps give losses ' +
          ', '.join(f'{v:.4f}' for v in losses[:6]) + ' ...')
    print(f'[step] after 12 steps the loss is {losses[-1]:.6f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    xs = np.arange(9)
    before_vals = [PARAMS[k] for k in NAMES]
    after_vals = [after[k] for k in NAMES]
    ax.bar(xs - 0.19, before_vals, width=0.36, color='#f3f3f3', edgecolor=MUTED, lw=1.2,
           label='before the step')
    ax.bar(xs + 0.19, after_vals, width=0.36, color=LINK_PALE, edgecolor=LINK, lw=1.2,
           label='after one step')
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xticks(xs)
    ax.set_xticklabels(NAMES, fontsize=10)
    ax.set_ylabel('weight value', fontsize=10)
    ax.set_title(f'One step with learning rate {LR}: only the six weights with blame moved',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.set_ylim(-0.75, 1.5)

    ax = axes[1]
    _plot_style(ax)
    ax.plot(np.arange(len(losses)), losses, marker='o', color=LINK, lw=2.0, ms=5)
    ax.plot([0], [losses[0]], 'o', color=GRIP, ms=9)
    ax.plot([1], [losses[1]], 'o', color=SLIDE, ms=9)
    ax.annotate(f'{losses[0]:.4f}', xy=(0, losses[0]), xytext=(0.5, losses[0] + 0.03),
                fontsize=10, color=GRIP)
    ax.annotate(f'{losses[1]:.4f} after one step', xy=(1, losses[1]),
                xytext=(1.7, losses[1] + 0.06), fontsize=10, color=SLIDE,
                arrowprops=dict(arrowstyle='-|>', color=SLIDE, lw=1.0))
    ax.set_xlabel('steps taken', fontsize=10)
    ax.set_ylabel('loss on this one example', fontsize=10)
    ax.set_title(f'Repeating forward, backward and step drives the loss to '
                 f'{losses[-1]:.4f}', fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BP_DOC, 'one-step.svg')


# ==========================================================================
# PAGE 3, SECTION 4: automatic differentiation
# ==========================================================================

def the_tape() -> None:
    """What the framework writes down during the forward pass so it can go backwards."""
    f = FWD
    rows = [
        ('1', 'multiply and add', f'z1 = x1 x w11 + x2 x w21 + b1', f'{f["z1"]:.2f}',
         f'keeps x1 = {X1:.1f}, x2 = {X2:.1f}'),
        ('2', 'multiply and add', f'z2 = x1 x w12 + x2 x w22 + b2', f'{f["z2"]:.2f}',
         f'keeps x1 = {X1:.1f}, x2 = {X2:.1f}'),
        ('3', 'gate', 'h1 = z1 if z1 > 0 else 0', f'{f["h1"]:.2f}',
         f'keeps the sign of z1 = {f["z1"]:.2f}'),
        ('4', 'gate', 'h2 = z2 if z2 > 0 else 0', f'{f["h2"]:.2f}',
         f'keeps the sign of z2 = {f["z2"]:.2f}'),
        ('5', 'multiply and add', 'u = h1 x v1 + h2 x v2 + c', f'{f["u"]:.2f}',
         f'keeps h1 = {f["h1"]:.2f}, h2 = {f["h2"]:.2f}'),
        ('6', 'squared error', 'loss = (u - target) squared', f'{f["loss"]:.4f}',
         f'keeps u - target = {f["err"]:.2f}'),
    ]
    print('[tape] the recorded steps are ' + '; '.join(r[2] for r in rows))

    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _blank(ax, (0, 11.6), (0, 5.4))
    ax.text(5.8, 5.05, 'The tape the framework keeps while going forward, and reads while going back',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    heads = ['step', 'what it did', 'the arithmetic', 'value', 'what it had to keep']
    xcol = [0.35, 1.25, 3.3, 6.9, 8.0]
    y = 4.45
    for h, x in zip(heads, xcol):
        ax.text(x, y, h, fontsize=10.5, weight='bold', color=LINK)
    y -= 0.18
    ax.plot([0.3, 11.4], [y, y], color=LINK, lw=1.2)
    y -= 0.42
    for row in rows:
        _box(ax, 0.3, y - 0.17, 11.1, 0.56, face='#fafafa', edge='#eeeeee', lw=0.8)
        for value, x in zip(row, xcol):
            fam = 'monospace' if x in (3.3, 6.9) else None
            ax.text(x, y + 0.11, value, fontsize=10, color=INK, family=fam)
        y -= 0.64
    _arrow(ax, (11.52, 0.45), (11.52, 4.0), colour=GRIP, lw=2.2)
    ax.text(11.35, 2.2, 'the backward pass reads the tape upwards', rotation=90,
            ha='center', va='center', fontsize=10, color=GRIP, weight='bold')
    ax.text(0.35, 0.18, f'Nothing on the tape is a derivative written by hand: each kind of '
                        f'step knows its own slope.', fontsize=10.5, color=MUTED)
    _save(fig, BP_DOC, 'the-tape.svg')


def gradient_check() -> None:
    """Measured slopes against worked-out slopes, the check a framework's own tests use."""
    b = BWD
    eps = 1e-6
    exact, measured = [], []
    for k in NAMES:
        up, down = dict(PARAMS), dict(PARAMS)
        up[k] += eps
        down[k] -= eps
        m = (tiny_forward(up)['loss'] - tiny_forward(down)['loss']) / (2 * eps)
        exact.append(b['d' + k])
        measured.append(m)
    gap = float(np.max(np.abs(np.array(exact) - np.array(measured))))
    for k, e, m in zip(NAMES, exact, measured):
        print(f'[check] {k}: worked out {e:+.6f}, measured {m:+.6f}')
    print(f'[check] the largest gap between the two is {gap:.2e}')

    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plot_style(ax)
    xs = np.arange(9)
    ax.bar(xs - 0.19, exact, width=0.36, color=LINK_PALE, edgecolor=LINK, lw=1.3,
           label='worked out by the chain rule')
    ax.bar(xs + 0.19, measured, width=0.36, color='#d9efdc', edgecolor=SLIDE, lw=1.3,
           label='measured by nudging the weight')
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xticks(xs)
    ax.set_xticklabels(NAMES, fontsize=10.5)
    ax.set_ylim(-2.5, 0.75)
    ax.set_ylabel('slope of the loss against the weight', fontsize=10)
    ax.set_title(f'The two ways of getting the slope agree to within {gap:.0e}',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    _save(fig, BP_DOC, 'gradient-check.svg')


def activation_memory() -> None:
    """Where training memory actually goes: the kept activations, not the weights."""
    width, layers, batch, bytes_each = 1024, 12, 32, 4
    params = layers * (width * width + width)
    param_bytes = params * bytes_each
    acts = layers * 2 * batch * width          # the weighted sum and the gate output per layer
    act_bytes = acts * bytes_each
    grad_bytes = param_bytes
    state_bytes = 2 * param_bytes              # the two running averages an optimiser keeps
    print(f'[memory] a {layers}-layer network of width {width} has {params:,} weights '
          f'= {param_bytes / 1e6:.1f} MB at {bytes_each} bytes each')
    print(f'[memory] its gradients are another {grad_bytes / 1e6:.1f} MB and the '
          f'optimiser state {state_bytes / 1e6:.1f} MB')
    print(f'[memory] kept activations for a batch of {batch} are {acts:,} numbers '
          f'= {act_bytes / 1e6:.1f} MB')
    total = param_bytes + grad_bytes + state_bytes + act_bytes
    print(f'[memory] total {total / 1e6:.1f} MB, of which activations are '
          f'{100 * act_bytes / total:.0f} per cent')

    fig, ax = plt.subplots(figsize=(9.8, 4.8), facecolor='white')
    _plot_style(ax)
    labels = ['the weights', 'their gradients', 'the optimiser\nrunning averages',
              f'the kept activations\nfor a batch of {batch}']
    vals = [param_bytes / 1e6, grad_bytes / 1e6, state_bytes / 1e6, act_bytes / 1e6]
    colours = [LINK_PALE, '#d9efdc', '#f6e3c0', '#fde3e3']
    edges = [LINK, SLIDE, JOINT, GRIP]
    ax.bar(np.arange(4), vals, color=colours, edgecolor=edges, lw=1.5, width=0.62)
    for i, v in enumerate(vals):
        ax.text(i, v + 2.0, f'{v:.1f} MB', ha='center', fontsize=11, weight='bold', color=INK)
    ax.set_xticks(np.arange(4))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_ylabel('memory in megabytes', fontsize=10)
    ax.set_title(f'Four things live in memory while a {layers}-layer network of width {width} '
                 f'trains', fontsize=12, weight='bold')
    _save(fig, BP_DOC, 'activation-memory.svg')


def memory_vs_batch() -> None:
    """The weights cost the same whatever the batch; the activations grow with it."""
    width, layers, bytes_each = 1024, 12, 4
    params = layers * (width * width + width)
    param_bytes = params * bytes_each / 1e6
    batches = np.array([1, 2, 4, 8, 16, 32, 64, 128, 256])
    act = layers * 2 * batches * width * bytes_each / 1e6
    cross = batches[np.argmax(act > param_bytes)]
    print(f'[batch] the weights, their gradients and the optimiser state come to '
          f'{4 * param_bytes:.1f} MB whatever the batch is')
    for bsz, a in zip(batches, act):
        print(f'[batch] batch {bsz:>3}: activations {a:7.1f} MB')
    print(f'[batch] activations pass the {param_bytes:.1f} MB of weights at a batch of {cross}')

    fig, ax = plt.subplots(figsize=(9.8, 4.8), facecolor='white')
    _plot_style(ax)
    ax.plot(batches, act, marker='o', color=GRIP, lw=2.2, ms=6,
            label='kept activations')
    ax.axhline(param_bytes, color=LINK, lw=2.0, ls='--', label='the weights themselves')
    ax.axhline(4 * param_bytes, color=PURPLE, lw=2.0, ls=':',
               label='weights, gradients and optimiser state together')
    ax.set_xscale('log', base=2)
    ax.set_xticks(batches)
    ax.set_xticklabels([str(b) for b in batches])
    ax.set_xlabel('examples in the batch', fontsize=10)
    ax.set_ylabel('memory in megabytes', fontsize=10)
    ax.set_title(f'Doubling the batch doubles the activation memory and changes nothing else',
                 fontsize=12, weight='bold')
    ax.annotate(f'batch {cross}: the activations pass the weights',
                xy=(cross, act[np.argmax(act > param_bytes)]),
                xytext=(2.2, 1100), fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.1))
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, BP_DOC, 'memory-vs-batch.svg')
