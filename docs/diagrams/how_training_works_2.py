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
    ax.text(g0 + 1.9, lift0 + slope2 * 1.9 - 1.0, f'slope {slope2:.1f}', fontsize=10.5,
            color=GRIP, weight='bold')
    ax.text(g1 - 2.4, _stage_two(np.array([g1]))[0] + 3.2, f'slope {0.8 * g1:.1f}',
            fontsize=10.5, color=PURPLE, weight='bold')
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
    ax.text((len(steps) - 1) / 2, max(measured) * 1.10,
            f'the two slopes multiplied: {GEAR:.0f} x {0.8 * GEAR * a0:.1f} = {exact:.1f}',
            ha='center', fontsize=10.5, color=GRIP, weight='bold')
    for x, m in zip(xs, measured):
        ax.text(x, m + 0.2, f'{m:.3f}', ha='center', fontsize=10, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{s:g}' for s in steps])
    ax.set_ylim(0, max(measured) * 1.22)
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
LR: float = 0.05

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

    fig, ax = plt.subplots(figsize=(11.0, 5.4), facecolor='white')
    _blank(ax, (0, 11.0), (0, 5.4))
    r = 0.46
    xs, hs, us = 1.0, 4.3, 7.6
    y_top, y_bot, y_mid = 3.3, 1.3, 2.3
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

    ax.text(hs, y_top + r + 0.30, f'z1 = {f["z1"]:.2f}, above 0, so h1 = {f["h1"]:.2f}',
            ha='center', fontsize=10, color=LINK)
    ax.text(hs, y_bot - r - 0.40, f'z2 = {f["z2"]:.2f}, below 0, so h2 = {f["h2"]:.2f}',
            ha='center', fontsize=10, color=GRIP)

    _box(ax, 8.9, y_mid - 0.50, 1.9, 1.0, face='#fde3e3', edge=GRIP)
    ax.text(9.85, y_mid + 0.23, 'loss', ha='center', fontsize=10.5, color=INK)
    ax.text(9.85, y_mid - 0.18, f'{f["loss"]:.4f}', ha='center', fontsize=12,
            weight='bold', color=INK)
    _arrow(ax, (us + r, y_mid), (8.85, y_mid), colour=MUTED, lw=1.4)
    ax.text(8.25, y_mid - 0.75, f'target {TARGET:.1f}', ha='center', fontsize=9.5,
            color=MUTED)

    ax.text(5.5, 5.05, f'The forward pass: two inputs become {f["u"]:.2f}, '
                       f'and the target is {TARGET:.1f}',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    ax.text(5.5, 4.62, f'the three biases are b1 = {B1}, b2 = {B2} and c = {C}',
            ha='center', fontsize=10, color=MUTED)
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
                xy=(f['u'], f['loss']), xytext=(f['u'] - 1.45, 4.3), fontsize=10.5,
                color=INK, arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.2),
                bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                          edgecolor='none', alpha=0.95))
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

    fig, ax = plt.subplots(figsize=(11.2, 5.8), facecolor='white')
    _blank(ax, (0, 11.2), (0, 5.8))
    r = 0.46
    xs, hs, us = 1.0, 4.3, 7.6
    y_top, y_bot, y_mid = 3.5, 1.3, 2.4
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

    _box(ax, 8.9, y_mid - 0.50, 2.1, 1.0, face='#fde3e3', edge=GRIP)
    ax.text(9.95, y_mid + 0.23, 'loss', ha='center', fontsize=10.5, color=INK)
    ax.text(9.95, y_mid - 0.18, f'{f["loss"]:.4f}', ha='center', fontsize=12,
            weight='bold', color=INK)
    ax.text(8.35, y_mid + 0.60, f'dloss/du = {b["du"]:.2f}', ha='center', fontsize=10,
            color=GRIP, weight='bold')

    ax.text(hs, y_top + r + 0.30, f'dloss/dh1 = {b["dh1"]:.3f}, the gate is open, '
                                  f'so dloss/dz1 = {b["dz1"]:.3f}',
            ha='center', fontsize=10, color=LINK)
    ax.text(hs, y_bot - r - 0.40, f'dloss/dh2 = {b["dh2"]:.2f}, but the gate is shut, '
                                  f'so dloss/dz2 = {b["dz2"]:.2f}',
            ha='center', fontsize=10, color=GRIP)

    ax.text(5.6, 5.45, 'The backward pass: the blame starts at the loss and is handed '
                       'back along every line',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    ax.text(5.6, 5.02, f'the three biases take db1 = {b["db1"]:.3f}, '
                       f'db2 = {b["db2"]:.3f} and dc = {b["dc"]:.2f}',
            ha='center', fontsize=10, color=MUTED)
    _save(fig, BP_DOC, 'tiny-network-backward.svg')


def blame_bars() -> None:
    """All nine gradients side by side, so the reader can see which weight is blamed most."""
    b = BWD
    grads = [b['dw11'], b['dw21'], b['db1'], b['dw12'], b['dw22'], b['db2'],
             b['dv1'], b['dv2'], b['dc']]
    print('[blame] ' + ', '.join(f'{n}:{g:+.3f}' for n, g in zip(NAMES, grads)))
    top = float(np.max(np.abs(grads)))
    biggest = [n for n, g in zip(NAMES, grads) if abs(abs(g) - top) < 1e-12]
    print(f'[blame] the biggest share of the blame, {top:.3f}, belongs to '
          + ' and '.join(biggest))

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
    ax.set_xlim(-2.9, 2.2)
    ax.set_xlabel('value in the backward pass', fontsize=10)
    ax.set_title('Multiplying by the gate slope stops the blame at neuron 2',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
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
    ax.set_title(f'One step at learning rate {LR}: only the blamed weights move',
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
    ax.set_title(f'Repeating it drives the loss to {losses[-1]:.4f}',
                 fontsize=11.5, weight='bold')
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
    ax.legend(fontsize=9.5, frameon=False, loc='lower center')
    _save(fig, BP_DOC, 'gradient-check.svg')


POSITIONS: int = 512       # picture patches, or words, in one example
WIDTH: int = 1024
LAYERS: int = 12
BATCH: int = 32
BYTES: int = 4             # four bytes for each number, which is float32


def _weight_bytes() -> int:
    return LAYERS * (WIDTH * WIDTH + WIDTH) * BYTES


def _act_bytes(batch: int) -> int:
    """Two arrays kept per layer: what went in, and the weighted sum inside."""
    return LAYERS * 2 * batch * POSITIONS * WIDTH * BYTES


def activation_memory() -> None:
    """Where training memory actually goes: the kept activations, not the weights."""
    params = LAYERS * (WIDTH * WIDTH + WIDTH)
    param_bytes = _weight_bytes()
    act_bytes = _act_bytes(BATCH)
    grad_bytes = param_bytes
    state_bytes = 2 * param_bytes              # the two running averages an optimiser keeps
    kept = LAYERS * 2 * BATCH * POSITIONS * WIDTH
    print(f'[memory] a {LAYERS}-layer network of width {WIDTH} has {params:,} weights '
          f'= {param_bytes / 1e6:.1f} MB at {BYTES} bytes each')
    print(f'[memory] its gradients are another {grad_bytes / 1e6:.1f} MB and the '
          f'optimiser state {state_bytes / 1e6:.1f} MB')
    print(f'[memory] a batch of {BATCH} examples of {POSITIONS} positions makes '
          f'{kept:,} kept numbers = {act_bytes / 1e9:.2f} GB')
    total = param_bytes + grad_bytes + state_bytes + act_bytes
    print(f'[memory] total {total / 1e9:.2f} GB, of which activations are '
          f'{100 * act_bytes / total:.0f} per cent')

    fig, ax = plt.subplots(figsize=(10.0, 4.9), facecolor='white')
    _plot_style(ax)
    labels = ['the weights', 'their gradients', 'the optimiser\nrunning averages',
              f'the kept activations\nfor a batch of {BATCH}']
    vals = [param_bytes / 1e9, grad_bytes / 1e9, state_bytes / 1e9, act_bytes / 1e9]
    colours = [LINK_PALE, '#d9efdc', '#f6e3c0', '#fde3e3']
    edges = [LINK, SLIDE, JOINT, GRIP]
    ax.bar(np.arange(4), vals, color=colours, edgecolor=edges, lw=1.5, width=0.62)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.04, f'{v:.2f} GB', ha='center', fontsize=11, weight='bold', color=INK)
    ax.set_xticks(np.arange(4))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_ylabel('memory in gigabytes', fontsize=10)
    ax.set_title(f'A {LAYERS}-layer network of width {WIDTH} reading {POSITIONS} positions: '
                 f'the activations are {100 * act_bytes / total:.0f} per cent of the memory',
                 fontsize=12, weight='bold')
    _save(fig, BP_DOC, 'activation-memory.svg')


def memory_vs_batch() -> None:
    """The weights cost the same whatever the batch; the activations grow with it."""
    fixed = 4 * _weight_bytes() / 1e9
    batches = np.array([1, 2, 4, 8, 16, 32, 64])
    act = np.array([_act_bytes(int(b)) for b in batches]) / 1e9
    per_example = _act_bytes(1) / 1e9
    print(f'[batch] the weights, their gradients and the optimiser state come to '
          f'{fixed:.2f} GB whatever the batch is')
    print(f'[batch] one example of {POSITIONS} positions costs {per_example:.3f} GB '
          f'in kept activations')
    for bsz, a in zip(batches, act):
        print(f'[batch] batch {bsz:>3}: activations {a:6.2f} GB, '
              f'total {a + fixed:6.2f} GB')
    cross = int(batches[int(np.argmax(act > fixed))])
    print(f'[batch] the activations pass everything else put together at a batch of {cross}')

    fig, ax = plt.subplots(figsize=(10.0, 4.8), facecolor='white')
    _plot_style(ax)
    ax.plot(batches, act, marker='o', color=GRIP, lw=2.2, ms=6,
            label='kept activations')
    ax.plot(batches, act + fixed, marker='s', color=PURPLE, lw=2.0, ms=5,
            label='everything together')
    ax.axhline(fixed, color=LINK, lw=2.0, ls='--',
               label='weights, gradients and optimiser state')
    ax.set_xscale('log', base=2)
    ax.set_xticks(batches)
    ax.set_xticklabels([str(b) for b in batches])
    ax.set_xlabel('examples in the batch', fontsize=10)
    ax.set_ylabel('memory in gigabytes', fontsize=10)
    ax.set_title('Doubling the batch doubles the activation memory and changes nothing else',
                 fontsize=12, weight='bold')
    ax.annotate(f'batch {cross}: the activations pass everything else',
                xy=(cross, float(act[int(np.argmax(act > fixed))])),
                xytext=(1.05, 2.6), fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.1))
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, BP_DOC, 'memory-vs-batch.svg')


# ==========================================================================
# PAGE 3, SECTIONS 5 and 6: vanishing and exploding gradients, and the fixes
#
# A deep stack of layers, all the same width, written out in NumPy so that the
# forward pass and the backward pass are both real arithmetic. The loss is the
# average of the numbers the last layer gives, so the blame leaving the loss is
# the same size whatever the weights are, and the picture shows what the stack
# does to that blame on the way back.
# ==========================================================================

def deep_stack(depth: int, scale: float, seed: int = 7, width: int = 64,
               batch: int = 16, residual: bool = False,
               renormalise: bool = False,
               gate: str = 'relu') -> dict[str, list[float]]:
    """Run one deep stack forward and backward and measure three things.

    'acts' is the size of the numbers coming out of each layer, 'blame' is the
    size of the gradient arriving back at each layer boundary, and 'grad' is
    the size of each layer's own weight gradient. All three are a root mean
    square over the numbers in them, so stacks of any width compare.
    """
    rng = np.random.default_rng(seed)
    weights = [rng.normal(0.0, scale / np.sqrt(width), size=(width, width))
               for _ in range(depth)]
    hs: list[Arr] = [rng.normal(0.0, 1.0, size=(batch, width))]
    zs: list[Arr] = []
    scales: list[float] = []
    for layer in range(depth):
        z = hs[-1] @ weights[layer]
        a = np.maximum(z, 0.0) if gate == 'relu' else np.tanh(z)
        out = hs[-1] + a if residual else a
        if renormalise:
            s = float(np.sqrt(np.mean(out ** 2))) + 1e-12
            out = out / s
            scales.append(s)
        zs.append(z)
        hs.append(out)
    dh = np.full((batch, width), 1.0 / (batch * width))   # loss = the average output
    blame: list[float] = [float(np.sqrt(np.mean(dh ** 2)))]
    grad: list[float] = []
    for layer in range(depth - 1, -1, -1):
        if renormalise:
            dh = dh / scales[layer]
        da = dh
        slope = (zs[layer] > 0).astype(float) if gate == 'relu' else _tanh_slope(zs[layer])
        dz = da * slope
        grad.append(float(np.sqrt(np.mean((hs[layer].T @ dz) ** 2))))
        dh = dz @ weights[layer].T
        if residual:
            dh = dh + da
        blame.append(float(np.sqrt(np.mean(dh ** 2))))
    grad.reverse()
    blame.reverse()
    return {'acts': [float(np.sqrt(np.mean(a ** 2))) for a in hs],
            'blame': blame, 'grad': grad}


def _tanh_slope(z: Arr) -> Arr:
    return 1.0 - np.tanh(z) ** 2


def multiplying_many_numbers() -> None:
    """Why a long chain of multiplications ends at nearly nothing or at far too much."""
    n = np.arange(0, 61)
    factors = [0.6, 0.9, 1.0, 1.1, 1.4]
    colours = [GRIP, WRIST, INK, TEAL, PURPLE]
    for fac in factors:
        print(f'[chainsize] {fac} multiplied by itself: 10 gives {fac ** 10:.3g}, '
              f'30 gives {fac ** 30:.3g}, 60 gives {fac ** 60:.3g}')
    fig, ax = plt.subplots(figsize=(10.0, 5.0), facecolor='white')
    _plot_style(ax)
    for fac, colour in zip(factors, colours):
        ax.plot(n, np.power(fac, n.astype(float)), color=colour, lw=2.2,
                label=f'each layer multiplies by {fac}')
    ax.set_yscale('log')
    ax.set_ylim(1e-14, 1e10)
    ax.axhline(1.0, color=MUTED, lw=1.0, ls='--')
    ax.set_xlabel('layers the blame has passed through', fontsize=10)
    ax.set_ylabel('what the blame has been multiplied by (log scale)', fontsize=10)
    ax.set_title(f'A chain of 60 layers multiplies 0.6 down to {0.6 ** 60:.0e} '
                 f'and 1.4 up to {1.4 ** 60:.0e}',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    _save(fig, BP_DOC, 'multiplying-many-numbers.svg')


def _sigmoid(z: Arr) -> Arr:
    return 1.0 / (1.0 + np.exp(-z))


def sigmoid_slope() -> None:
    """The old smooth activation function and the reason it stopped being used."""
    z = np.linspace(-6, 6, 600)
    s = _sigmoid(z)
    slope = s * (1 - s)
    top = float(slope.max())
    rng = np.random.default_rng(3)
    sample = rng.normal(0.0, 1.0, size=200_000)
    mean_slope = float(np.mean(_sigmoid(sample) * (1 - _sigmoid(sample))))
    print(f'[sigmoid] the steepest the slope ever gets is {top:.4f}, at z = 0')
    print(f'[sigmoid] for inputs drawn from a standard bell curve the average slope '
          f'is {mean_slope:.4f}')
    for depth in (5, 10, 30):
        print(f'[sigmoid] {depth} layers of the steepest slope give {top ** depth:.3g}, '
              f'and of the average slope {mean_slope ** depth:.3g}')
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    ax.plot(z, s, color=LINK, lw=2.4, label='the activation function')
    ax.plot(z, slope, color=GRIP, lw=2.4, label='its slope')
    ax.axhline(top, color=GRIP, lw=1.0, ls='--')
    ax.text(-5.8, top + 0.06, f'the slope never passes {top:.2f}', fontsize=10, color=GRIP)
    ax.plot([0], [top], 'o', color=GRIP, ms=7)
    ax.set_xlabel('the weighted sum, z', fontsize=10)
    ax.set_ylabel('value', fontsize=10)
    ax.set_title('The smooth S-shaped activation and its slope', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center left')

    ax = axes[1]
    _plot_style(ax)
    depths = np.arange(1, 31)
    ax.plot(depths, top ** depths, color=GRIP, lw=2.2, marker='o', ms=4,
            label=f'the best case, {top:.2f} each layer')
    ax.plot(depths, mean_slope ** depths, color=PURPLE, lw=2.2, marker='s', ms=4,
            label=f'the usual case, {mean_slope:.2f} each layer')
    ax.set_yscale('log')
    ax.set_xlabel('layers', fontsize=10)
    ax.set_ylabel('what the blame is multiplied by (log scale)', fontsize=10)
    ax.set_title(f'Thirty such layers shrink the blame to {top ** 30:.0e} at best',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    fig.tight_layout()
    _save(fig, BP_DOC, 'sigmoid-slope.svg')


VANISH: float = 0.7        # starting weights too small: the blame dies out
BALANCE: float = 1.414     # the scale that keeps the sizes level with a ReLU gate
EXPLODE: float = 2.0       # starting weights too large: the blame runs away


def gradient_by_layer() -> None:
    """Real sizes of the blame as it travels back, at three depths and three weight scales."""
    depths = [10, 30, 60]
    settings = [(VANISH, GRIP, f'starting weights too small (scale {VANISH})'),
                (BALANCE, SLIDE, f'starting weights well chosen (scale {BALANCE:.2f})'),
                (EXPLODE, PURPLE, f'starting weights too large (scale {EXPLODE:.1f})')]
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3), facecolor='white')
    for ax, depth in zip(axes, depths):
        _plot_style(ax)
        for scale, colour, label in settings:
            out = deep_stack(depth, scale)
            b = out['blame']
            ax.plot(np.arange(depth + 1), b, color=colour, lw=2.0,
                    label=label if depth == depths[0] else None)
            print(f'[bylayer] depth {depth:>2}, scale {scale}: blame at the output '
                  f'{b[-1]:.3e}, at the input {b[0]:.3e}, '
                  f'multiplied by {b[0] / b[-1]:.3e} on the way')
        ax.set_yscale('log')
        ax.set_ylim(1e-25, 1e10)
        ax.set_yticks([1e-24, 1e-18, 1e-12, 1e-6, 1e0, 1e6])
        ax.set_xlabel('layer the blame has reached', fontsize=10)
        if depth == depths[0]:
            ax.set_ylabel('size of the blame arriving there (log scale)', fontsize=10)
        ax.set_title(f'{depth} layers', fontsize=11.5, weight='bold')
    axes[0].legend(fontsize=9, frameon=False, loc='lower right')
    fig.suptitle('The blame travels from right to left: with the wrong starting scale it '
                 'dies out or runs away before it reaches layer 1',
                 fontsize=12.5, weight='bold', y=1.03)
    fig.tight_layout()
    _save(fig, BP_DOC, 'gradient-by-layer.svg')


def residual_gradient() -> None:
    """A plain deep stack against the same stack with residual connections added."""
    depth = 50
    plain = deep_stack(depth, VANISH)
    res = deep_stack(depth, VANISH, residual=True)
    both = deep_stack(depth, VANISH, residual=True, renormalise=True)
    print(f'[residual] plain stack of {depth} layers: the blame falls from '
          f'{plain["blame"][-1]:.3e} at the output to {plain["blame"][0]:.3e} at the input')
    print(f'[residual] with residual connections it goes from {res["blame"][-1]:.3e} '
          f'to {res["blame"][0]:.3e}')
    print(f'[residual] the residual stack hands layer 1 '
          f'{res["blame"][0] / plain["blame"][0]:.3g} times the blame the plain one does')
    print(f'[residual] residual plus rescaling: {both["blame"][-1]:.3e} at the output, '
          f'{both["blame"][0]:.3e} at the input')
    print(f'[residual] plain activations fall from {plain["acts"][0]:.3f} to '
          f'{plain["acts"][-1]:.3e}; residual ones grow to {res["acts"][-1]:.3e}; '
          f'rescaled they stay at {both["acts"][-1]:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor='white')
    xs = np.arange(depth + 1)
    ax = axes[0]
    _plot_style(ax)
    ax.plot(xs, plain['blame'], color=GRIP, lw=2.2, label='plain: h = gate(h x W)')
    ax.plot(xs, res['blame'], color=PURPLE, lw=2.2, label='residual: h = h + gate(h x W)')
    ax.plot(xs, both['blame'], color=SLIDE, lw=2.2, label='residual, each layer rescaled')
    ax.set_yscale('log')
    ax.set_xlabel('layer the blame has reached', fontsize=10)
    ax.set_ylabel('size of the blame arriving there (log scale)', fontsize=10)
    ax.set_title(f'{depth} layers, the same starting weights in all three',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower right')

    ax = axes[1]
    _plot_style(ax)
    ax.plot(xs, plain['acts'], color=GRIP, lw=2.2, label='plain')
    ax.plot(xs, res['acts'], color=PURPLE, lw=2.2, label='residual')
    ax.plot(xs, both['acts'], color=SLIDE, lw=2.2, label='residual, each layer rescaled')
    ax.set_yscale('log')
    ax.set_xlabel('layer, counting from the input', fontsize=10)
    ax.set_ylabel('size of the numbers coming out (log scale)', fontsize=10)
    ax.set_title('The residual path keeps the forward numbers alive, then grows them',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower left')
    fig.tight_layout()
    _save(fig, BP_DOC, 'residual-gradient.svg')


def normalisation_rescue() -> None:
    """Rescaling each layer's output keeps the numbers, and the blame, in range."""
    depth = 40
    runs = {
        f'scale {EXPLODE:.1f}, as it is': (deep_stack(depth, EXPLODE), PURPLE, '-'),
        f'scale {EXPLODE:.1f}, rescaled': (deep_stack(depth, EXPLODE, renormalise=True),
                                           PURPLE, '--'),
        f'scale {VANISH}, as it is': (deep_stack(depth, VANISH), GRIP, '-'),
        f'scale {VANISH}, rescaled': (deep_stack(depth, VANISH, renormalise=True),
                                      GRIP, '--'),
    }
    for name, (out, _c, _ls) in runs.items():
        print(f'[norm] {name:24s} activations end at {out["acts"][-1]:.3e}, '
              f'blame at the input {out["blame"][0]:.3e}')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor='white')
    xs = np.arange(depth + 1)
    ax = axes[0]
    _plot_style(ax)
    for name, (out, colour, ls) in runs.items():
        ax.plot(xs, out['acts'], color=colour, lw=2.2, ls=ls, label=name)
    ax.set_yscale('log')
    ax.set_ylim(1e-16, 1e9)
    ax.set_xlabel('layer, counting from the input', fontsize=10)
    ax.set_ylabel('size of the numbers coming out (log scale)', fontsize=10)
    ax.set_title('Rescaling every layer holds the forward numbers at 1',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower left')

    ax = axes[1]
    _plot_style(ax)
    for name, (out, colour, ls) in runs.items():
        ax.plot(xs, out['blame'], color=colour, lw=2.2, ls=ls, label=name)
    ax.set_yscale('log')
    ax.set_xlabel('layer the blame has reached', fontsize=10)
    ax.set_ylabel('size of the blame arriving there (log scale)', fontsize=10)
    ax.set_title('And it holds the blame level all the way back',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    fig.tight_layout()
    _save(fig, BP_DOC, 'normalisation-rescue.svg')


def _erf(z: Arr) -> Arr:
    return np.vectorize(__import__('math').erf)(z)


def activation_slopes() -> None:
    """The four activation rules and the slopes they hand back, which is what matters."""
    z = np.linspace(-4, 4, 1601)
    s = _sigmoid(z)
    curves = {
        'S-shaped (sigmoid)': (s * (1 - s), GRIP),
        'tanh': (1.0 - np.tanh(z) ** 2, WRIST),
        'rectified linear unit': ((z > 0).astype(float), LINK),
        'GELU': (0.5 * (1 + _erf(z / np.sqrt(2))) +
                 z * np.exp(-z ** 2 / 2) / np.sqrt(2 * np.pi), SLIDE),
    }
    tops = {name: float(np.max(slope)) for name, (slope, _c) in curves.items()}
    for name, top in tops.items():
        print(f'[slopes] {name:22s} steepest slope {top:.3f}, '
              f'and 30 of those multiply to {top ** 30:.3g}')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    for name, (slope, colour) in curves.items():
        ax.plot(z, slope, color=colour, lw=2.2, label=name)
    ax.axhline(1.0, color=MUTED, lw=1.0, ls='--')
    ax.set_ylim(-0.25, 1.35)
    ax.set_xlabel('the weighted sum, z', fontsize=10)
    ax.set_ylabel('slope handed back', fontsize=10)
    ax.set_title('What each rule multiplies the blame by', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')

    ax = axes[1]
    _plot_style(ax)
    names = list(tops)
    vals = [tops[n] for n in names]
    colours = [curves[n][1] for n in names]
    ax.bar(np.arange(4), vals, color=colours, edgecolor=INK, lw=0.8, width=0.6)
    for i, n in enumerate(names):
        ax.text(i, tops[n] + 0.03, f'{tops[n]:.2f}', ha='center', fontsize=11, color=INK)
        ax.text(i, 0.08, f'30 layers\nof that:\n{tops[n] ** 30:.1e}', ha='center',
                fontsize=9, color='white')
    ax.set_xticks(np.arange(4))
    ax.set_xticklabels(['sigmoid', 'tanh', 'ReLU', 'GELU'], fontsize=10.5)
    ax.set_ylim(0, 1.35)
    ax.set_ylabel('the steepest slope the rule can hand back', fontsize=10)
    ax.set_title('Only the S-shaped rule shrinks the blame even at its steepest',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, BP_DOC, 'activation-slopes.svg')


def clipping_run() -> None:
    """A real run where a few odd examples make huge gradients, with and without clipping."""
    rng = np.random.default_rng(11)
    n, batch, steps = 512, 16, 240
    x = rng.normal(0.0, 1.0, size=n)
    true_w, true_b = 2.0, -0.5
    clean = true_w * x + true_b + rng.normal(0.0, 0.1, size=n)
    y = clean.copy()
    spoilt = rng.choice(n, size=6, replace=False)
    y[spoilt] += rng.normal(0.0, 120.0, size=6)
    keep = np.setdiff1d(np.arange(n), spoilt)
    print(f'[clip] {len(spoilt)} of the {n} targets were spoilt, the worst of them '
          f'{np.max(np.abs(y[spoilt])):.0f} instead of about '
          f'{np.max(np.abs(clean[spoilt])):.1f}')

    def run(clip: float | None) -> tuple[list[float], list[float], list[float]]:
        w, b, lr = 0.0, 0.0, 0.12
        losses, norms, dists = [], [], []
        gen = np.random.default_rng(5)
        for _ in range(steps):
            idx = gen.choice(n, size=batch, replace=False)
            err = w * x[idx] + b - y[idx]
            gw = float(2.0 * np.mean(err * x[idx]))
            gb = float(2.0 * np.mean(err))
            size = float(np.sqrt(gw ** 2 + gb ** 2))
            norms.append(size)
            if clip is not None and size > clip:
                gw, gb = gw * clip / size, gb * clip / size
            w -= lr * gw
            b -= lr * gb
            losses.append(float(np.mean((w * x[keep] + b - clean[keep]) ** 2)))
            dists.append(float(np.hypot(w - true_w, b - true_b)))
        return losses, norms, dists

    no_clip, norms, no_dist = run(None)
    threshold = 10.0
    clipped, _, clip_dist = run(threshold)
    print(f'[clip] the biggest gradient size in the run was {max(norms):.1f}, '
          f'against a middling {float(np.median(norms)):.2f}')
    print(f'[clip] {sum(1 for v in norms if v > threshold)} of the {steps} steps '
          f'had a gradient above the threshold of {threshold:.0f}')
    print(f'[clip] loss on the unspoilt examples after {steps} steps: '
          f'{no_clip[-1]:.3f} without clipping, {clipped[-1]:.3f} with it')
    print(f'[clip] worst loss along the way: {max(no_clip):.1f} without clipping, '
          f'{max(clipped):.1f} with it')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    ax.plot(np.arange(steps), norms, color=MUTED, lw=1.1)
    ax.axhline(threshold, color=GRIP, lw=2.0, ls='--')
    ax.text(steps * 0.42, threshold * 2.6, f'clip anything above {threshold:.0f}',
            fontsize=10.5, color=GRIP, weight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))
    ax.set_yscale('log')
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('size of the gradient (log scale)', fontsize=10)
    ax.set_title(f'Most steps are quiet, a few are '
                 f'{max(norms) / float(np.median(norms)):.0f} times bigger',
                 fontsize=11.5, weight='bold')

    ax = axes[1]
    _plot_style(ax)
    ax.plot(np.arange(steps), no_clip, color=GRIP, lw=2.0, label='no clipping')
    ax.plot(np.arange(steps), clipped, color=SLIDE, lw=2.0,
            label=f'gradient size clipped at {threshold:.0f}')
    ax.set_yscale('log')
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('loss on the unspoilt examples (log scale)', fontsize=10)
    ax.set_title(f'Clipping holds the damage to one slow step instead of '
                 f'{max(no_clip):.0f}', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    fig.tight_layout()
    _save(fig, BP_DOC, 'clipping-run.svg')


# ==========================================================================
# PAGE 4: the training loop
#
# One small network, written out in NumPy, trained by hand-written stochastic
# gradient descent, momentum, Adam and AdamW. The data is simulated: four
# input numbers drawn from a seeded generator and a target from a fixed smooth
# formula plus noise, which stands in for any job with a few inputs and one
# number to predict.
# ==========================================================================

N_TRAIN: int = 960
N_VAL: int = 240
D_IN: int = 4
HIDDEN: int = 32
BATCH_SIZE: int = 32
EPOCHS: int = 20


def make_data(seed: int = 0, n_train: int = N_TRAIN, n_val: int = N_VAL
              ) -> tuple[Arr, Arr, Arr, Arr]:
    """Simulated data: four inputs, and one target from a fixed smooth formula plus noise."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, size=(n_train + n_val, D_IN))
    y = (np.sin(1.5 * x[:, 0]) + 0.5 * x[:, 1] * x[:, 2] - 0.3 * x[:, 3] ** 2
         + 0.2 * rng.normal(0.0, 1.0, size=n_train + n_val))
    return x[:n_train], y[:n_train], x[n_train:], y[n_train:]


def init_params(hidden: int = HIDDEN, seed: int = 1, mode: str = 'he',
                scale: float = 0.0) -> dict[str, Arr]:
    """Starting weights. 'he' uses the scale that keeps the layer sizes level."""
    rng = np.random.default_rng(seed)
    if mode == 'zero':
        w1 = np.zeros((D_IN, hidden))
        w2 = np.zeros((hidden, 1))
    elif mode == 'same':
        w1 = np.full((D_IN, hidden), 0.3)
        w2 = np.full((hidden, 1), 0.3)
    else:
        s1 = np.sqrt(2.0 / D_IN) if mode == 'he' else scale
        s2 = np.sqrt(2.0 / hidden) if mode == 'he' else scale
        w1 = rng.normal(0.0, s1, size=(D_IN, hidden))
        w2 = rng.normal(0.0, s2, size=(hidden, 1))
    return {'w1': w1, 'b1': np.zeros(hidden), 'w2': w2, 'b2': np.zeros(1)}


def forward_backward(p: dict[str, Arr], x: Arr, y: Arr
                     ) -> tuple[float, dict[str, Arr], Arr]:
    """One forward pass, one backward pass, the squared error averaged over the batch."""
    z1 = x @ p['w1'] + p['b1']
    h = np.maximum(z1, 0.0)
    out = (h @ p['w2'] + p['b2'])[:, 0]
    err = out - y
    loss = float(np.mean(err ** 2))
    dout = (2.0 * err / len(y))[:, None]
    g = {'w2': h.T @ dout, 'b2': dout.sum(axis=0)}
    dh = dout @ p['w2'].T
    dz1 = dh * (z1 > 0)
    g['w1'] = x.T @ dz1
    g['b1'] = dz1.sum(axis=0)
    return loss, g, h


def eval_loss(p: dict[str, Arr], x: Arr, y: Arr) -> float:
    h = np.maximum(x @ p['w1'] + p['b1'], 0.0)
    return float(np.mean(((h @ p['w2'] + p['b2'])[:, 0] - y) ** 2))


def lr_at(step: int, total: int, base: float, schedule: str,
          warm: int = 60) -> float:
    """The learning rate this step gets, under one of three schedules."""
    if schedule == 'constant':
        return base
    if schedule == 'cosine':
        return base * 0.5 * (1.0 + np.cos(np.pi * step / total))
    if schedule == 'warmcos':
        if step < warm:
            return base * (step + 1) / warm
        t = (step - warm) / max(total - warm, 1)
        return base * 0.5 * (1.0 + np.cos(np.pi * t))
    raise ValueError(schedule)


def train(optimiser: str = 'sgd', lr: float = 0.05, epochs: int = EPOCHS,
          batch: int = BATCH_SIZE, schedule: str = 'constant',
          hidden: int = HIDDEN, init: str = 'he', init_scale: float = 0.0,
          decay: float = 0.0, seed: int = 1, data_seed: int = 0,
          zero_grads: bool = True, n_train: int = N_TRAIN,
          momentum: float = 0.9, warm: int = 60) -> dict[str, list[float]]:
    """Run the loop, and keep the loss at every step and at the end of every epoch."""
    xt, yt, xv, yv = make_data(data_seed, n_train=n_train)
    p = init_params(hidden, seed, init, init_scale)
    state = {k: np.zeros_like(v) for k, v in p.items()}
    state2 = {k: np.zeros_like(v) for k, v in p.items()}
    running = {k: np.zeros_like(v) for k, v in p.items()}
    gen = np.random.default_rng(seed + 100)
    per_epoch = len(xt) // batch
    total = per_epoch * epochs
    step_loss: list[float] = []
    grad_size: list[float] = []
    lrs: list[float] = []
    train_curve: list[float] = []
    val_curve: list[float] = []
    weight_size: list[float] = []
    step = 0
    for _ in range(epochs):
        order = gen.permutation(len(xt))
        for k in range(per_epoch):
            idx = order[k * batch:(k + 1) * batch]
            loss, g, _ = forward_backward(p, xt[idx], yt[idx])
            if not zero_grads:                      # the bug: gradients pile up
                for key in g:
                    running[key] = running[key] + g[key]
                g = {key: running[key] for key in g}
            now = lr_at(step, total, lr, schedule, warm)
            lrs.append(now)
            grad_size.append(float(np.sqrt(sum(float(np.sum(v ** 2)) for v in g.values()))))
            for key in p:
                if optimiser == 'sgd':
                    p[key] = p[key] - now * g[key]
                elif optimiser == 'momentum':
                    state[key] = momentum * state[key] + g[key]
                    p[key] = p[key] - now * state[key]
                else:
                    grad = g[key] + (decay * p[key] if optimiser == 'adam' else 0.0)
                    state[key] = 0.9 * state[key] + 0.1 * grad
                    state2[key] = 0.999 * state2[key] + 0.001 * grad ** 2
                    mhat = state[key] / (1 - 0.9 ** (step + 1))
                    vhat = state2[key] / (1 - 0.999 ** (step + 1))
                    p[key] = p[key] - now * mhat / (np.sqrt(vhat) + 1e-8)
                    if optimiser == 'adamw':
                        p[key] = p[key] - now * decay * p[key]
            step_loss.append(loss)
            step += 1
        train_curve.append(eval_loss(p, xt, yt))
        val_curve.append(eval_loss(p, xv, yv))
        weight_size.append(float(np.sqrt(sum(float(np.sum(v ** 2)) for v in p.values()))))
    return {'step_loss': step_loss, 'train': train_curve, 'val': val_curve,
            'lrs': lrs, 'grad': grad_size, 'weights': weight_size,
            'per_epoch': [float(per_epoch)], 'total': [float(total)]}


def loop_order() -> None:
    """The seven lines of the loop, in the order a computer runs them."""
    steps = [
        ('1', 'take the next batch', f'{BATCH_SIZE} examples off the shuffled list'),
        ('2', 'forward pass', 'work out what the network says for all of them'),
        ('3', 'work out the loss', 'one number for how wrong the batch was'),
        ('4', 'backward pass', 'one gradient for every weight'),
        ('5', 'step', 'the optimiser moves every weight a little'),
        ('6', 'set the gradients back to zero', 'or the next batch adds to these'),
        ('7', 'go back to line 1', 'until the examples run out'),
    ]
    tail = [
        ('after each pass through the data', 'work out the loss on the held-back examples'),
        ('after each pass through the data', 'write the weights to a file: a checkpoint'),
    ]
    print('[loop] ' + ' -> '.join(s[1] for s in steps))
    fig, ax = plt.subplots(figsize=(10.8, 7.6), facecolor='white')
    _blank(ax, (0, 10.8), (0, 7.6))
    ax.text(5.4, 7.25, 'One step of training is seven lines, always in this order',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    y = 6.5
    for num, name, what in steps:
        _box(ax, 0.5, y - 0.22, 9.3, 0.58, face=LINK_PALE if num != '6' else '#fde3e3',
             edge=LINK if num != '6' else GRIP)
        ax.text(0.85, y + 0.06, num, fontsize=11.5, weight='bold', color=INK)
        ax.text(1.35, y + 0.06, name, fontsize=11.5, color=INK)
        ax.text(5.0, y + 0.06, what, fontsize=10.5, color=MUTED)
        y -= 0.72
    _arrow(ax, (10.0, y + 0.5), (10.0, 6.6), colour=LINK, lw=1.8)
    ax.text(10.45, 4.3, 'repeat', rotation=90, ha='center', va='center',
            fontsize=10.5, color=LINK, weight='bold')
    y -= 0.18
    for when, what in tail:
        _box(ax, 0.5, y - 0.22, 9.3, 0.58, face='#d9efdc', edge=SLIDE)
        ax.text(0.85, y + 0.06, when, fontsize=10, color=MUTED)
        ax.text(5.0, y + 0.06, what, fontsize=11, color=INK)
        y -= 0.72
    _save(fig, TL_DOC, 'loop-order.svg')


def batches_and_epochs() -> None:
    """How many steps a run has: the examples divided by the batch, times the passes."""
    per_epoch = N_TRAIN // BATCH_SIZE
    total = per_epoch * EPOCHS
    seen = total * BATCH_SIZE
    print(f'[counting] {N_TRAIN} examples in batches of {BATCH_SIZE} give '
          f'{per_epoch} steps in one pass through the data')
    print(f'[counting] {EPOCHS} passes give {total} steps, and the network is shown '
          f'{seen:,} examples in all, each one {EPOCHS} times')
    fig, ax = plt.subplots(figsize=(10.8, 4.6), facecolor='white')
    _blank(ax, (0, 10.8), (0, 4.6))
    ax.text(5.4, 4.3, f'{N_TRAIN} examples, batches of {BATCH_SIZE}: '
                      f'{per_epoch} steps in one pass, {total} steps in {EPOCHS} passes',
            ha='center', fontsize=12.5, weight='bold', color=INK)
    w, gap = 0.30, 0.025
    x0 = 0.45
    for k in range(per_epoch):
        _box(ax, x0 + k * (w + gap), 2.75, w, 0.7,
             face=LINK_PALE if k else '#f6c9c9', edge=LINK if k else GRIP)
    ax.text(x0 + 0.15, 3.6, 'the first batch', fontsize=9.5, color=GRIP, ha='center')
    ax.text(5.4, 2.42, f'one pass through the data: {per_epoch} batches of {BATCH_SIZE} '
                       f'= {per_epoch * BATCH_SIZE} examples',
            ha='center', fontsize=10.5, color=INK)
    for e in range(EPOCHS):
        _box(ax, x0 + e * (0.48 + 0.03), 1.2, 0.48, 0.6, face='#d9efdc', edge=SLIDE)
        ax.text(x0 + 0.24 + e * 0.51, 1.5, f'{e + 1}', ha='center', va='center',
                fontsize=8.5, color=INK)
    ax.text(5.4, 0.82, f'{EPOCHS} passes, so {total} steps in all, and each example '
                       f'is used {EPOCHS} times',
            ha='center', fontsize=10.5, color=INK)
    ax.text(5.4, 0.35, 'A pass through the whole training set is called an epoch, and '
                       'the loss on the held-back examples is checked at the end of each one',
            ha='center', fontsize=10, color=MUTED)
    _save(fig, TL_DOC, 'batches-and-epochs.svg')


def loss_per_step() -> None:
    """What the loss does step by step inside one run, and what the epoch average hides."""
    run = train('sgd', lr=0.05, epochs=EPOCHS)
    per_epoch = int(run['per_epoch'][0])
    steps = np.arange(len(run['step_loss']))
    avg = [float(np.mean(run['step_loss'][e * per_epoch:(e + 1) * per_epoch]))
           for e in range(EPOCHS)]
    first = run['step_loss'][:per_epoch]
    print(f'[perstep] the first batch gives a loss of {first[0]:.3f} and the '
          f'thirtieth {first[-1]:.3f}, but they jump about on the way')
    print(f'[perstep] the biggest and smallest batch losses in the first pass are '
          f'{max(first):.3f} and {min(first):.3f}')
    print(f'[perstep] the average batch loss falls from {avg[0]:.3f} in the first pass '
          f'to {avg[-1]:.3f} in the twentieth')
    fig, ax = plt.subplots(figsize=(10.4, 4.8), facecolor='white')
    _plot_style(ax)
    ax.plot(steps, run['step_loss'], color=LINK_PALE, lw=1.0, label='one batch')
    mids = np.arange(EPOCHS) * per_epoch + per_epoch / 2
    ax.plot(mids, avg, color=GRIP, lw=2.4, marker='o', ms=5,
            label='average over one pass through the data')
    ax.set_yscale('log')
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('squared error on the batch (log scale)', fontsize=10)
    ax.set_title(f'Every batch gives a different loss, and the average of {per_epoch} of '
                 f'them falls from {avg[0]:.2f} to {avg[-1]:.2f}',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    _save(fig, TL_DOC, 'loss-per-step.svg')


def forgetting_to_zero() -> None:
    """What happens when line 6 is left out and every batch adds to the last one's gradient."""
    good = train('sgd', lr=0.02, epochs=6, zero_grads=True)
    bad = train('sgd', lr=0.02, epochs=6, zero_grads=False)
    print(f'[zero] with the gradients zeroed each step, the loss after 6 passes is '
          f'{good["train"][-1]:.4f}')
    print(f'[zero] with them left to pile up it is {bad["train"][-1]:.4g}')
    print(f'[zero] the gradient size grows from {bad["grad"][0]:.3f} to '
          f'{bad["grad"][-1]:.3g} when they are never cleared, against '
          f'{good["grad"][-1]:.3f} when they are')
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    ax.plot(np.arange(len(good['step_loss'])), good['step_loss'], color=SLIDE, lw=1.4,
            label='gradients zeroed every step')
    ax.plot(np.arange(len(bad['step_loss'])), bad['step_loss'], color=GRIP, lw=1.4,
            label='line 6 left out')
    ax.set_yscale('log')
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('loss on the batch (log scale)', fontsize=10)
    ax.set_title('Leaving out one line ruins the run', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')

    ax = axes[1]
    _plot_style(ax)
    ax.plot(np.arange(len(good['grad'])), good['grad'], color=SLIDE, lw=1.6,
            label='gradients zeroed every step')
    ax.plot(np.arange(len(bad['grad'])), bad['grad'], color=GRIP, lw=1.6,
            label='line 6 left out')
    ax.set_yscale('log')
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('size of the gradient used (log scale)', fontsize=10)
    ax.set_title('The piled-up gradients grow without limit', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='center right')
    fig.tight_layout()
    _save(fig, TL_DOC, 'forgetting-to-zero.svg')


# --------------------------------------------------------------------------
# PAGE 4, SECTIONS 2 and 3: momentum, Adam and AdamW
#
# A bowl with two weights, steep in one direction and shallow in the other,
# which is the shape that makes plain steps slow.
# --------------------------------------------------------------------------

STEEP: float = 200.0       # one weight the loss cares about a thousand times more
SHALLOW: float = 0.2
START: tuple[float, float] = (-0.9, -4.0)
LR_PLAIN: float = 0.009    # the largest learning rate plain steps survive here
LR_ADAM: float = 0.1


def bowl_loss(a: Arr | float, b: Arr | float) -> Arr | float:
    return 0.5 * (STEEP * np.asarray(a) ** 2 + SHALLOW * np.asarray(b) ** 2)


def bowl_run(rule: str, lr: float, steps: int = 60, mu: float = 0.9,
             decay: float = 0.0) -> dict[str, Arr]:
    """Walk downhill on the bowl with one of four rules, keeping everything on the way."""
    a, b = START
    va = vb = ma = mb = sa = sb = 0.0
    path, losses, ms, vs, moves = [], [], [], [], []
    for t in range(steps):
        ga, gb = STEEP * a, SHALLOW * b
        path.append((a, b))
        losses.append(float(bowl_loss(a, b)))
        if rule == 'sgd':
            da, db = lr * ga, lr * gb
        elif rule == 'momentum':
            va, vb = mu * va + ga, mu * vb + gb
            da, db = lr * va, lr * vb
            ms.append((va, vb))
        else:
            if rule == 'adam':
                ga, gb = ga + decay * a, gb + decay * b
            ma, mb = 0.9 * ma + 0.1 * ga, 0.9 * mb + 0.1 * gb
            sa, sb = 0.999 * sa + 0.001 * ga ** 2, 0.999 * sb + 0.001 * gb ** 2
            c1, c2 = 1 - 0.9 ** (t + 1), 1 - 0.999 ** (t + 1)
            da = lr * (ma / c1) / (np.sqrt(sa / c2) + 1e-8)
            db = lr * (mb / c1) / (np.sqrt(sb / c2) + 1e-8)
            ms.append((ma / c1, mb / c1))
            vs.append((np.sqrt(sa / c2), np.sqrt(sb / c2)))
        moves.append((da, db))
        a, b = a - da, b - db
        if rule == 'adamw':
            a, b = a - lr * decay * a, b - lr * decay * b
    return {'path': np.array(path), 'loss': np.array(losses),
            'm': np.array(ms) if ms else np.zeros((0, 2)),
            'v': np.array(vs) if vs else np.zeros((0, 2)),
            'move': np.array(moves)}


def _bowl_contours(ax: Axes) -> None:
    aa = np.linspace(-1.15, 1.15, 300)
    bb = np.linspace(-4.7, 1.7, 300)
    ag, bg = np.meshgrid(aa, bb)
    levels = [0.02, 0.1, 0.5, 2.0, 8.0, 20.0, 45.0, 80.0, 130.0]
    ax.contour(ag, bg, bowl_loss(ag, bg), levels=levels, colors=GRID, linewidths=0.9)
    ax.plot([0], [0], 'x', color=INK, ms=10, mew=2)
    ax.text(0.06, 0.12, 'the lowest point', fontsize=9.5, color=INK)


def momentum_path() -> None:
    """Plain steps against steps with momentum, on the same bowl."""
    plain = bowl_run('sgd', LR_PLAIN, steps=200)
    mom = bowl_run('momentum', LR_PLAIN, steps=200)
    print(f'[momentum] the bowl is {STEEP / SHALLOW:.0f} times steeper in one direction '
          f'than the other')
    print(f'[momentum] after 200 steps plain descent is at '
          f'({plain["path"][-1][0]:+.4f}, {plain["path"][-1][1]:+.4f}) '
          f'with loss {plain["loss"][-1]:.4f}')
    print(f'[momentum] with momentum 0.9 it is at '
          f'({mom["path"][-1][0]:+.4f}, {mom["path"][-1][1]:+.4f}) '
          f'with loss {mom["loss"][-1]:.4f}')
    fig, ax = plt.subplots(figsize=(9.8, 5.2), facecolor='white')
    _plot_style(ax)
    _bowl_contours(ax)
    ax.plot(plain['path'][:, 0], plain['path'][:, 1], color=GRIP, lw=1.8, marker='o',
            ms=3.0, label=f'plain steps, learning rate {LR_PLAIN}')
    ax.plot(mom['path'][:, 0], mom['path'][:, 1], color=SLIDE, lw=1.8, marker='o',
            ms=3.0, label=f'momentum 0.9, learning rate {LR_PLAIN}')
    ax.plot([START[0]], [START[1]], 'o', color=INK, ms=8)
    ax.text(START[0] + 0.04, START[1] - 0.26, 'both start here', fontsize=9.5, color=INK)
    ax.set_xlabel('the steep weight', fontsize=10)
    ax.set_ylabel('the shallow weight', fontsize=10)
    ax.set_title('Plain steps zigzag across the steep direction; momentum builds up speed '
                 'along the shallow one', fontsize=12, weight='bold')
    ax.annotate(f'200 plain steps end here,\nstill {abs(plain["path"][-1][1]):.1f} '
                f'from the bottom',
                xy=(plain['path'][-1][0], plain['path'][-1][1]),
                xytext=(-1.12, -1.35), ha='left', fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.1))
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, TL_DOC, 'momentum-path.svg')


def momentum_loss() -> None:
    """How much faster momentum gets down the same bowl."""
    plain = bowl_run('sgd', LR_PLAIN, steps=400)
    mom = bowl_run('momentum', LR_PLAIN, steps=400)
    target = 0.01
    reach_p = int(np.argmax(plain['loss'] < target)) if np.any(plain['loss'] < target) else -1
    reach_m = int(np.argmax(mom['loss'] < target)) if np.any(mom['loss'] < target) else -1
    print(f'[momentum] to get the loss below {target}, plain descent needs '
          f'{reach_p} steps and momentum needs {reach_m}')
    print(f'[momentum] after 400 steps the two losses are {plain["loss"][-1]:.3f} '
          f'and {mom["loss"][-1]:.2e}')
    fig, ax = plt.subplots(figsize=(9.8, 4.8), facecolor='white')
    _plot_style(ax)
    ax.plot(plain['loss'], color=GRIP, lw=2.2, label='plain steps')
    ax.plot(mom['loss'], color=SLIDE, lw=2.2, label='momentum 0.9')
    ax.axhline(target, color=MUTED, lw=1.0, ls='--')
    ax.plot([reach_m], [mom['loss'][reach_m]], 'o', color=SLIDE, ms=8)
    ax.annotate(f'momentum gets there in {reach_m} steps', xy=(reach_m, target),
                xytext=(reach_m + 30, target * 20), fontsize=10, color=SLIDE,
                arrowprops=dict(arrowstyle='-|>', color=SLIDE, lw=1.0))
    ax.annotate(f'plain steps never get there in 400', xy=(380, plain['loss'][380]),
                xytext=(150, 8.0), fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.0))
    ax.set_yscale('log')
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('loss on the bowl (log scale)', fontsize=10)
    ax.set_title(f'Momentum reaches a loss of {target} in {reach_m} steps, and plain '
                 f'steps are still at {plain["loss"][-1]:.2f} after 400',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    _save(fig, TL_DOC, 'momentum-loss.svg')


def momentum_average() -> None:
    """The running average inside momentum: it cancels the zigzag and adds up the steady pull."""
    mom = bowl_run('momentum', LR_PLAIN, steps=60)
    raw_a = STEEP * mom['path'][:, 0]
    raw_b = SHALLOW * mom['path'][:, 1]
    vel = mom['m']
    print(f'[average] in the shallow direction the gradient stays near '
          f'{raw_b[0]:.2f} and the running average grows to {vel[:, 1].min():.2f}, '
          f'{vel[:, 1].min() / raw_b[0]:.1f} times as big')
    print(f'[average] in the steep direction the gradient swings between '
          f'{raw_a.min():+.2f} and {raw_a.max():+.2f}, so the running average stays '
          f'within {np.abs(vel[:, 0]).max():.2f}')
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    ax.plot(raw_a, color=MUTED, lw=1.6, marker='o', ms=3, label='the gradient this step')
    ax.plot(vel[:, 0], color=GRIP, lw=2.2, label='the running average')
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('value', fontsize=10)
    ax.set_title('The steep weight: the swings cancel out', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')

    ax = axes[1]
    _plot_style(ax)
    ax.plot(raw_b, color=MUTED, lw=1.6, marker='o', ms=3, label='the gradient this step')
    ax.plot(vel[:, 1], color=SLIDE, lw=2.2, label='the running average')
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('value', fontsize=10)
    ax.set_title(f'The shallow weight: the pulls add up to '
                 f'{vel[:, 1].min() / raw_b[0]:.1f} times one gradient',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    fig.tight_layout()
    _save(fig, TL_DOC, 'momentum-average.svg')


def adam_paths() -> None:
    """Three rules on the same bowl: plain steps, momentum, and a step size for each weight."""
    plain = bowl_run('sgd', LR_PLAIN, steps=200)
    mom = bowl_run('momentum', LR_PLAIN, steps=200)
    adam = bowl_run('adamw', LR_ADAM, steps=200)
    for name, run in (('plain', plain), ('momentum', mom), ('Adam', adam)):
        print(f'[adam] after 200 steps {name:9s} is at '
              f'({run["path"][-1][0]:+.5f}, {run["path"][-1][1]:+.5f}), '
              f'loss {run["loss"][-1]:.3e}')
    fig, ax = plt.subplots(figsize=(9.8, 5.2), facecolor='white')
    _plot_style(ax)
    _bowl_contours(ax)
    ax.plot(plain['path'][:, 0], plain['path'][:, 1], color=GRIP, lw=1.7, marker='o',
            ms=3.2, label='plain steps')
    ax.plot(mom['path'][:, 0], mom['path'][:, 1], color=SLIDE, lw=1.7, marker='o',
            ms=3.2, label='momentum 0.9')
    ax.plot(adam['path'][:, 0], adam['path'][:, 1], color=PURPLE, lw=2.0, marker='o',
            ms=3.2, label=f'Adam, learning rate {LR_ADAM}')
    ax.plot([START[0]], [START[1]], 'o', color=INK, ms=8)
    ax.set_xlabel('the steep weight', fontsize=10)
    ax.set_ylabel('the shallow weight', fontsize=10)
    ax.set_title('Adam gives each weight its own step size, so it walks almost straight down',
                 fontsize=12, weight='bold')
    ax.annotate('200 plain steps\nend here', xy=(plain['path'][-1][0], plain['path'][-1][1]),
                xytext=(-1.12, -1.6), ha='left', fontsize=10, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.1))
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, TL_DOC, 'adam-paths.svg')


def adam_inside() -> None:
    """What Adam keeps for each weight, and the step that comes out of the two averages."""
    adam = bowl_run('adamw', LR_ADAM, steps=120)
    m, v, move = adam['m'], adam['v'], adam['move']
    print(f'[inside] the steep weight starts with a gradient of '
          f'{STEEP * START[0]:+.1f} and the shallow one with {SHALLOW * START[1]:+.1f}, '
          f'{abs(STEEP * START[0] / (SHALLOW * START[1])):.1f} times apart')
    print(f'[inside] at step 10 Adam divides by {v[9, 0]:.3f} for the steep weight and '
          f'{v[9, 1]:.3f} for the shallow one')
    print(f'[inside] so the two moves at step 10 are {move[9, 0]:+.4f} and '
          f'{move[9, 1]:+.4f}, within a factor of '
          f'{abs(move[9, 0] / move[9, 1]):.2f} of each other')
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    steps = np.arange(len(m))
    ax.plot(steps, np.abs(m[:, 0]), color=GRIP, lw=2.0,
            label='steep weight: average gradient')
    ax.plot(steps, v[:, 0], color=GRIP, lw=2.0, ls='--',
            label='steep weight: average size')
    ax.plot(steps, np.abs(m[:, 1]), color=SLIDE, lw=2.0,
            label='shallow weight: average gradient')
    ax.plot(steps, v[:, 1], color=SLIDE, lw=2.0, ls='--',
            label='shallow weight: average size')
    ax.set_yscale('log')
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('value (log scale)', fontsize=10)
    ax.set_title('The two averages Adam keeps per weight', fontsize=11.5, weight='bold')
    ax.legend(fontsize=8.5, frameon=False, loc='lower left')

    ax = axes[1]
    _plot_style(ax)
    ax.plot(steps, np.abs(move[:, 0]), color=GRIP, lw=2.2, label='steep weight')
    ax.plot(steps, np.abs(move[:, 1]), color=SLIDE, lw=2.2, label='shallow weight')
    ax.set_yscale('log')
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('size of the move (log scale)', fontsize=10)
    ax.set_title('Dividing by the second one evens the moves out',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    fig.tight_layout()
    _save(fig, TL_DOC, 'adam-inside.svg')


def decay_rules(decay: float, lr: float = 0.02, steps: int = 3000
                ) -> dict[str, Arr]:
    """Two ways of shrinking weights, on a bowl whose best answer is 1 for both weights."""
    out: dict[str, Arr] = {}
    for rule in ('adam_l2', 'adamw'):
        a = b = 0.0
        ma = mb = sa = sb = 0.0
        hist = []
        for t in range(steps):
            ga, gb = STEEP * (a - 1.0), SHALLOW * (b - 1.0)
            if rule == 'adam_l2':
                ga, gb = ga + decay * a, gb + decay * b
            ma, mb = 0.9 * ma + 0.1 * ga, 0.9 * mb + 0.1 * gb
            sa, sb = 0.999 * sa + 0.001 * ga ** 2, 0.999 * sb + 0.001 * gb ** 2
            c1, c2 = 1 - 0.9 ** (t + 1), 1 - 0.999 ** (t + 1)
            a -= lr * (ma / c1) / (np.sqrt(sa / c2) + 1e-8)
            b -= lr * (mb / c1) / (np.sqrt(sb / c2) + 1e-8)
            if rule == 'adamw':
                a -= lr * decay * a
                b -= lr * decay * b
            hist.append((a, b))
        out[rule] = np.array(hist)
    return out


def adamw_decay() -> None:
    """Why AdamW keeps the shrinking apart from the gradient."""
    main = decay_rules(0.5)
    l2, dec = main['adam_l2'], main['adamw']
    print(f'[decay] the best answer for both weights is 1.0')
    print(f'[decay] with the shrink added to the gradient, Adam ends at '
          f'{l2[-1][0]:.4f} for the steep weight and {l2[-1][1]:.4f} for the shallow one')
    print(f'[decay] with the shrink kept separate, AdamW ends at {dec[-1][0]:.4f} '
          f'and {dec[-1][1]:.4f}, the same shrink for both')
    strengths = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    ends = {k: [] for k in ('l2_steep', 'l2_shallow', 'w_steep', 'w_shallow')}
    for st in strengths:
        r = decay_rules(st)
        ends['l2_steep'].append(r['adam_l2'][-1][0])
        ends['l2_shallow'].append(r['adam_l2'][-1][1])
        ends['w_steep'].append(r['adamw'][-1][0])
        ends['w_shallow'].append(r['adamw'][-1][1])
        print(f'[decay] shrink {st:>4}: added to the gradient gives '
              f'{r["adam_l2"][-1][0]:.3f} and {r["adam_l2"][-1][1]:.3f}; '
              f'kept separate gives {r["adamw"][-1][0]:.3f} and '
              f'{r["adamw"][-1][1]:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    steps = np.arange(len(l2))
    ax.plot(steps, l2[:, 0], color=GRIP, lw=2.0, label='shrink in the gradient: steep weight')
    ax.plot(steps, l2[:, 1], color=GRIP, lw=2.0, ls='--',
            label='shrink in the gradient: shallow weight')
    ax.plot(steps, dec[:, 0], color=SLIDE, lw=2.0, label='shrink kept separate: steep weight')
    ax.plot(steps, dec[:, 1], color=SLIDE, lw=2.0, ls='--',
            label='shrink kept separate: shallow weight')
    ax.axhline(1.0, color=MUTED, lw=1.0, ls=':')
    ax.text(1500, 1.04, 'the answer with no shrinking at all', fontsize=9.5, color=MUTED)
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('weight value', fontsize=10)
    ax.set_title('The same shrink setting, two ways of applying it',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=8.5, frameon=False, loc='lower right')

    ax = axes[1]
    _plot_style(ax)
    ax.plot(strengths, ends['l2_steep'], color=GRIP, lw=2.0, marker='o', ms=5,
            label='in the gradient: steep weight')
    ax.plot(strengths, ends['l2_shallow'], color=GRIP, lw=2.0, ls='--', marker='s', ms=5,
            label='in the gradient: shallow weight')
    ax.plot(strengths, ends['w_steep'], color=SLIDE, lw=2.0, marker='o', ms=5,
            label='kept separate: steep weight')
    ax.plot(strengths, ends['w_shallow'], color=SLIDE, lw=2.4, ls='--', marker='s', ms=5,
            label='kept separate: shallow weight')
    ax.set_xscale('log')
    ax.set_xticks(strengths)
    ax.set_xticklabels([str(s) for s in strengths])
    ax.set_xlabel('how strong the shrink is', fontsize=10)
    ax.set_ylabel('where the weight ends up', fontsize=10)
    ax.set_title('Kept separate, both weights shrink by the same share',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=8.5, frameon=False, loc='lower left')
    fig.tight_layout()
    _save(fig, TL_DOC, 'adamw-decay.svg')


# --------------------------------------------------------------------------
# PAGE 4, SECTION 4: learning-rate schedules and warmup
# --------------------------------------------------------------------------

BASE_LR: float = 0.2
BIG_LR: float = 0.4
WARM: int = 60
SCHED_EPOCHS: int = 40


def schedule_curves() -> None:
    """The three schedules, drawn as the learning rate each step gets."""
    per_epoch = N_TRAIN // BATCH_SIZE
    total = per_epoch * SCHED_EPOCHS
    steps = np.arange(total)
    curves = {
        'constant': np.array([lr_at(s, total, BASE_LR, 'constant') for s in steps]),
        'cosine decay': np.array([lr_at(s, total, BASE_LR, 'cosine') for s in steps]),
        f'warmup over {WARM} steps, then cosine':
            np.array([lr_at(s, total, BASE_LR, 'warmcos', WARM) for s in steps]),
    }
    for name, c in curves.items():
        print(f'[schedule] {name:40s} starts at {c[0]:.4f}, '
              f'is {c[total // 2]:.4f} halfway, and ends at {c[-1]:.5f}')
    fig, ax = plt.subplots(figsize=(10.0, 4.6), facecolor='white')
    _plot_style(ax)
    for (name, c), colour in zip(curves.items(), (GRIP, LINK, SLIDE)):
        ax.plot(steps, c, color=colour, lw=2.4, label=name)
    ax.axvline(WARM, color=MUTED, lw=1.0, ls=':')
    ax.text(WARM + 18, BASE_LR * 0.40, f'warmup ends at step {WARM}', fontsize=9.5,
            color=MUTED)
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('learning rate', fontsize=10)
    ax.set_title(f'Three schedules over the {total} steps of a {SCHED_EPOCHS}-pass run, '
                 f'all starting from {BASE_LR}', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    _save(fig, TL_DOC, 'schedule-curves.svg')


def schedule_loss() -> None:
    """What the three schedules do to the loss of the same run."""
    runs = {
        'constant': train('sgd', lr=BASE_LR, schedule='constant', epochs=SCHED_EPOCHS),
        'cosine decay': train('sgd', lr=BASE_LR, schedule='cosine', epochs=SCHED_EPOCHS),
        'warmup then cosine': train('sgd', lr=BASE_LR, schedule='warmcos',
                                    warm=WARM, epochs=SCHED_EPOCHS),
    }
    for name, r in runs.items():
        print(f'[schedloss] {name:22s} ends with training loss {r["train"][-1]:.4f} '
              f'and held-back loss {r["val"][-1]:.4f}')
    best = min(runs, key=lambda k: runs[k]['val'][-1])
    print(f'[schedloss] the lowest held-back loss comes from {best}')
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    for (name, r), colour in zip(runs.items(), (GRIP, LINK, SLIDE)):
        ax.plot(np.arange(1, SCHED_EPOCHS + 1), r['train'], color=colour, lw=2.2,
                label=name)
    ax.set_yscale('log')
    ax.set_xlabel('passes through the data', fontsize=10)
    ax.set_ylabel('training loss (log scale)', fontsize=10)
    ax.set_title('The same network, the same data, three schedules',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')

    ax = axes[1]
    _plot_style(ax)
    names = list(runs)
    finals = [runs[n]['val'][-1] for n in names]
    ax.bar(np.arange(3), finals, color=[LINK_PALE, '#f6e3c0', '#d9efdc'],
           edgecolor=[LINK, JOINT, SLIDE], lw=1.5, width=0.58)
    for i, v in enumerate(finals):
        ax.text(i, v + 0.002, f'{v:.4f}', ha='center', fontsize=11, color=INK)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(['constant', 'cosine\ndecay', 'warmup then\ncosine'], fontsize=10)
    ax.set_ylim(0, max(finals) * 1.25)
    ax.set_ylabel('loss on the held-back examples at the end', fontsize=10)
    ax.set_title('Warming up, then letting the rate fall away, finishes lowest',
                 fontsize=11.5, weight='bold')
    fig.tight_layout()
    _save(fig, TL_DOC, 'schedule-loss.svg')


def warmup_blowup() -> None:
    """A learning rate too big to start with, with and without warmup."""
    flat = train('sgd', lr=BIG_LR, schedule='constant', epochs=SCHED_EPOCHS)
    warm = train('sgd', lr=BIG_LR, schedule='warmcos', warm=WARM, epochs=SCHED_EPOCHS)
    ok = train('sgd', lr=BASE_LR, schedule='warmcos', warm=WARM, epochs=SCHED_EPOCHS)
    flat_steps = np.array(flat['step_loss'])
    died = int(np.argmax(~np.isfinite(flat_steps))) if not np.all(np.isfinite(flat_steps)) else -1
    print(f'[warmup] with a flat learning rate of {BIG_LR} the loss stops being a '
          f'number at step {died}')
    print(f'[warmup] the same {BIG_LR} with {WARM} warmup steps ends at a training loss '
          f'of {warm["train"][-1]:.4f} and a held-back loss of {warm["val"][-1]:.4f}')
    print(f'[warmup] the safe rate of {BASE_LR} with the same warmup ends at '
          f'{ok["train"][-1]:.4f} and {ok["val"][-1]:.4f}')
    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plot_style(ax)
    ceiling = 1e6
    show = np.where(np.isfinite(flat_steps) & (flat_steps < ceiling), flat_steps, np.nan)
    ax.plot(np.arange(len(show)), show, color=GRIP, lw=1.4,
            label=f'learning rate {BIG_LR} from the first step')
    ax.plot(np.arange(len(warm['step_loss'])), warm['step_loss'], color=SLIDE, lw=1.4,
            label=f'learning rate {BIG_LR} after {WARM} warmup steps')
    ax.plot(np.arange(len(ok['step_loss'])), ok['step_loss'], color=LINK, lw=1.4,
            label=f'learning rate {BASE_LR} after {WARM} warmup steps')
    if died > 0:
        ax.axvline(died, color=GRIP, lw=1.0, ls=':')
        ax.annotate(f'no longer a number\nfrom step {died}', xy=(died, 1e4),
                    xytext=(died + 55, 3e5), fontsize=10, color=GRIP,
                    arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.0))
    ax.set_yscale('log')
    ax.set_ylim(1e-3, 1e7)
    ax.set_xlabel('step', fontsize=10)
    ax.set_ylabel('loss on the batch (log scale)', fontsize=10)
    ax.set_title(f'The same {BIG_LR} that ruins the run works once the first {WARM} steps '
                 f'build up to it', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    _save(fig, TL_DOC, 'warmup-blowup.svg')


# --------------------------------------------------------------------------
# PAGE 4, SECTION 5: where the weights start
# --------------------------------------------------------------------------

HE_SCALE: float = float(np.sqrt(2.0 / D_IN))
TINY_SCALE: float = 0.05
HUGE_SCALE: float = 3.0


def _first_batch(mode: str, scale: float = 0.0) -> tuple[float, float, Arr]:
    xt, yt, _xv, _yv = make_data(0)
    p = init_params(HIDDEN, 1, mode, scale)
    loss, g, h = forward_backward(p, xt[:BATCH_SIZE], yt[:BATCH_SIZE])
    size = float(np.sqrt(sum(float(np.sum(v ** 2)) for v in g.values())))
    return loss, size, h


def init_zero() -> None:
    """Two bad starts: all zero, and all the same."""
    _l0, _g0, h_zero = _first_batch('zero')
    _l1, _g1, h_same = _first_batch('same')
    _l2, _g2, h_he = _first_batch('he')
    xt, yt, _xv, _yv = make_data(0)
    p_same = init_params(HIDDEN, 1, 'same')
    _loss, g_same, _h = forward_backward(p_same, xt[:BATCH_SIZE], yt[:BATCH_SIZE])
    col = g_same['w1'][0]
    print(f'[zerostart] with every weight 0 the 32 hidden outputs are all '
          f'{h_zero[0].max():.1f}')
    print(f'[zerostart] with every weight the same the hidden outputs are all '
          f'{h_same[0][0]:.4f}, so the spread across the 32 neurons is '
          f'{h_same[0].std():.1e}')
    print(f'[zerostart] with the chosen random start the outputs run from '
          f'{h_he[0].min():.3f} to {h_he[0].max():.3f}')
    print(f'[zerostart] the 32 gradients for the first input weight of each neuron are '
          f'all {col[0]:+.5f}, spread {col.std():.1e}, so the neurons can never differ')
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    idx = np.arange(HIDDEN)
    ax.plot(idx, h_he[0], 'o', color=SLIDE, ms=5, label='the chosen random start')
    ax.plot(idx, h_same[0], 's', color=GRIP, ms=5, label='every weight the same')
    ax.plot(idx, h_zero[0], '^', color=PURPLE, ms=5, label='every weight zero')
    ax.set_xlabel('hidden neuron', fontsize=10)
    ax.set_ylabel('what that neuron gives for one example', fontsize=10)
    ax.set_ylim(-0.08, 1.05)
    ax.set_title(f'{HIDDEN} neurons, one example', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper right', ncol=2,
              columnspacing=1.0, handletextpad=0.4)

    ax = axes[1]
    _plot_style(ax)
    ax.plot(idx, g_same['w1'][0], 's', color=GRIP, ms=5,
            label='every weight the same')
    p_he = init_params(HIDDEN, 1, 'he')
    _l, g_he, _h = forward_backward(p_he, xt[:BATCH_SIZE], yt[:BATCH_SIZE])
    ax.plot(idx, g_he['w1'][0], 'o', color=SLIDE, ms=5, label='the chosen random start')
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xlabel('hidden neuron', fontsize=10)
    ax.set_ylabel('gradient for that neuron\'s first input weight', fontsize=10)
    ax.set_ylim(-0.33, 0.52)
    ax.set_title('Identical neurons are handed identical blame',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower center', ncol=2,
              columnspacing=1.0, handletextpad=0.4)
    fig.tight_layout()
    _save(fig, TL_DOC, 'init-zero.svg')


def init_scales() -> None:
    """What the size of the starting weights does to the very first batch."""
    rows = [('much too small', 'plain', TINY_SCALE),
            (f'the chosen scale ({HE_SCALE:.3f})', 'he', 0.0),
            ('much too large', 'plain', HUGE_SCALE)]
    data = []
    for label, mode, scale in rows:
        loss, size, h = _first_batch(mode, scale)
        hidden = float(np.sqrt(np.mean(h ** 2)))
        data.append((label, hidden, loss, size))
        print(f'[initscale] {label:28s} hidden numbers {hidden:.4f}, '
              f'first loss {loss:.4f}, first gradient {size:.4f}')
    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plot_style(ax)
    xs = np.arange(3)
    width = 0.26
    series = [('size of the hidden numbers', [d[1] for d in data], LINK_PALE, LINK),
              ('loss on the first batch', [d[2] for d in data], '#fde3e3', GRIP),
              ('size of the first gradient', [d[3] for d in data], '#d9efdc', SLIDE)]
    for k, (name, vals, face, edge) in enumerate(series):
        ax.bar(xs + (k - 1) * width, vals, width=width, color=face, edgecolor=edge,
               lw=1.4, label=name)
        for x, v in zip(xs + (k - 1) * width, vals):
            ax.text(x, v * 1.35, f'{v:.3g}', ha='center', fontsize=9, color=INK)
    ax.set_yscale('log')
    ax.set_ylim(1e-2, 1e7)
    ax.set_xticks(xs)
    ax.set_xticklabels([d[0] for d in data], fontsize=10.5)
    ax.set_ylabel('value, on a log scale', fontsize=10)
    ax.set_title('Starting weights three sizes apart give a first loss four orders apart',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, TL_DOC, 'init-scales.svg')


def init_loss() -> None:
    """Five starts, the same run, the same data."""
    xt, yt, _xv, _yv = make_data(0)
    spread = float(np.var(yt))
    runs = {
        'every weight zero': (train('sgd', lr=0.05, init='zero'), PURPLE),
        'every weight the same': (train('sgd', lr=0.05, init='same'), WRIST),
        f'much too small ({TINY_SCALE})': (train('sgd', lr=0.05, init='plain',
                                                 init_scale=TINY_SCALE), LINK),
        f'the chosen scale ({HE_SCALE:.3f})': (train('sgd', lr=0.05, init='he'), SLIDE),
        f'much too large ({HUGE_SCALE}): no line, because it is '
        f'not a number': (train('sgd', lr=0.05, init='plain',
                                init_scale=HUGE_SCALE), GRIP),
    }
    print(f'[initloss] guessing the average of the targets every time gives a loss of '
          f'{spread:.4f}')
    for name, (r, _c) in runs.items():
        end = r['train'][-1]
        label = 'no longer a number' if not np.isfinite(end) else f'{end:.4f}'
        print(f'[initloss] {name:30s} ends at {label} '
              f'(first pass {r["train"][0]:.4f})')
    fig, ax = plt.subplots(figsize=(10.2, 4.9), facecolor='white')
    _plot_style(ax)
    for name, (r, colour) in runs.items():
        curve = np.array(r['train'])
        curve = np.where(np.isfinite(curve) & (curve < 1e6), curve, np.nan)
        ax.plot(np.arange(1, EPOCHS + 1), curve, color=colour, lw=2.2, marker='o',
                ms=3.5, label=name)
    ax.axhline(spread, color=MUTED, lw=1.4, ls='--')
    ax.set_ylim(top=spread * 1.8)
    ax.text(EPOCHS * 0.5, spread * 1.10, 'the loss you get by always guessing the average',
            fontsize=9.5, color=MUTED, va='bottom', ha='center')
    ax.set_yscale('log')
    ax.set_xlabel('passes through the data', fontsize=10)
    ax.set_ylabel('training loss (log scale)', fontsize=10)
    ax.set_title('The all-zero start never leaves the average, and the much too large '
                 'start leaves the numbers altogether', fontsize=12, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower left')
    _save(fig, TL_DOC, 'init-loss.svg')


# --------------------------------------------------------------------------
# PAGE 4, SECTION 6: reading the curve, the time a run takes, checkpoints
# --------------------------------------------------------------------------

SMALL_SET: int = 24
OVERFIT_EPOCHS: int = 500


def overfit_run() -> dict[str, list[float]]:
    return train('adamw', lr=0.02, epochs=OVERFIT_EPOCHS, batch=8, hidden=256,
                 n_train=SMALL_SET)


def training_curve() -> None:
    """The picture every run is read from: the training loss, the held-back loss, and the gap."""
    r = overfit_run()
    t = np.array(r['train'])
    v = np.array(r['val'])
    best = int(np.argmin(v))
    print(f'[curve] with only {SMALL_SET} training examples the training loss falls from '
          f'{t[0]:.3f} to {t[-1]:.5f}')
    print(f'[curve] the held-back loss is lowest at pass {best + 1}, at {v[best]:.3f}, '
          f'and has risen to {v[-1]:.3f} by pass {OVERFIT_EPOCHS}')
    print(f'[curve] so the gap between them grows from {v[0] - t[0]:+.3f} to '
          f'{v[-1] - t[-1]:+.3f}')
    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plot_style(ax)
    xs = np.arange(1, OVERFIT_EPOCHS + 1)
    ax.fill_between(xs, t, v, color='#fde3e3', alpha=0.7, label='the gap')
    ax.plot(xs, t, color=LINK, lw=2.2, label='loss on the training examples')
    ax.plot(xs, v, color=GRIP, lw=2.2, label='loss on the held-back examples')
    ax.plot([best + 1], [v[best]], 'o', color=INK, ms=8)
    ax.annotate(f'lowest held-back loss, {v[best]:.3f},\nat pass {best + 1}: '
                f'the moment to stop',
                xy=(best + 1, v[best]), xytext=(best + 30, 2.2), fontsize=10, color=INK,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.1))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('passes through the data (log scale)', fontsize=10)
    ax.set_ylabel('squared error (log scale)', fontsize=10)
    ax.set_title(f'The training loss keeps falling to {t[-1]:.5f} while the held-back '
                 f'loss turns round and rises to {v[-1]:.3f}',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    _save(fig, TL_DOC, 'training-curve.svg')


def curve_shapes() -> None:
    """Four shapes a curve takes, and what each one is telling you."""
    healthy = train('sgd', lr=0.1, epochs=SCHED_EPOCHS)
    slow = train('sgd', lr=0.002, epochs=SCHED_EPOCHS)
    toobig = train('sgd', lr=0.22, epochs=SCHED_EPOCHS)
    over = overfit_run()
    print(f'[shapes] a good rate of 0.1 takes the training loss from '
          f'{healthy["train"][0]:.3f} to {healthy["train"][-1]:.4f}')
    print(f'[shapes] a rate of 0.002 is still at {slow["train"][-1]:.3f} after '
          f'{SCHED_EPOCHS} passes, and still falling')
    print(f'[shapes] a rate of 0.22 spikes to {max(toobig["step_loss"]):.0f} on single '
          f'batches and ends at {toobig["train"][-1]:.3f}')
    print(f'[shapes] the small-data run ends with training {over["train"][-1]:.5f} '
          f'and held-back {over["val"][-1]:.3f}')
    panels = [
        ('Still falling, nothing wrong', healthy, 'both curves fall together',
         SCHED_EPOCHS),
        ('The rate is too small', slow, 'slow but straight', SCHED_EPOCHS),
        ('The rate is too large', toobig, 'it jumps about and settles high',
         SCHED_EPOCHS),
        ('Too little data for the size of the network', over,
         'training falls, held back rises', OVERFIT_EPOCHS),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.4), facecolor='white')
    for ax, (title, run, note, epochs) in zip(axes.ravel(), panels):
        _plot_style(ax)
        xs = np.arange(1, epochs + 1)
        ax.plot(xs, run['train'], color=LINK, lw=2.0, label='training')
        ax.plot(xs, run['val'], color=GRIP, lw=2.0, label='held back')
        ax.set_yscale('log')
        if epochs == OVERFIT_EPOCHS:
            ax.set_xscale('log')
        ax.set_xlabel('passes through the data', fontsize=9.5)
        ax.set_ylabel('squared error (log scale)', fontsize=9.5)
        ax.set_title(title, fontsize=11.5, weight='bold')
        ax.text(0.03, 0.05, note, transform=ax.transAxes, fontsize=9.5, color=MUTED,
                zorder=10, bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                                     edgecolor='none', alpha=0.95))
        ax.legend(fontsize=9, frameon=False, loc='upper right')
    fig.suptitle('Four shapes, read from four real runs of the same network',
                 fontsize=12.5, weight='bold', y=1.0)
    fig.tight_layout()
    _save(fig, TL_DOC, 'curve-shapes.svg')


def step_time() -> None:
    """How much arithmetic one step is, and the hours that turns into."""
    widths = [64, 128, 256, 512, 1024, 2048]
    batch = 128
    mults = [5 * batch * w * w for w in widths]
    for w, m in zip(widths, mults):
        print(f'[arith] width {w:>5}: {2 * w * w:>12,} weights, and one step over a '
              f'batch of {batch} is {m:>15,} multiplications')
    print(f'[arith] doubling the width makes one step '
          f'{mults[1] / mults[0]:.0f} times as much arithmetic')
    counts = [1_000, 10_000, 100_000, 1_000_000]
    rates = [0.01, 0.1, 1.0]
    for r in rates:
        line = ', '.join(f'{c:,} steps = {c * r / 3600:.2f} hours' for c in counts)
        print(f'[arith] at {r} seconds a step: {line}')

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), facecolor='white')
    ax = axes[0]
    _plot_style(ax)
    ax.plot(widths, mults, color=LINK, lw=2.2, marker='o', ms=6)
    for w, m in zip(widths, mults):
        ax.annotate(f'{m / 1e6:.0f}M', xy=(w, m), xytext=(6, -14),
                    textcoords='offset points', ha='left', fontsize=9.5, color=INK)
    ax.set_xlim(widths[0] * 0.75, widths[-1] * 1.6)
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(widths)
    ax.set_xticklabels([str(w) for w in widths])
    ax.set_xlabel('width of the two layers', fontsize=10)
    ax.set_ylabel('multiplications in one step (log scale)', fontsize=10)
    ax.set_title(f'Arithmetic in one step, batch of {batch}',
                 fontsize=11.5, weight='bold')

    ax = axes[1]
    _plot_style(ax)
    for r, colour in zip(rates, (SLIDE, LINK, PURPLE)):
        ax.plot(counts, [c * r / 3600 for c in counts], color=colour, lw=2.2,
                marker='o', ms=5, label=f'{r} seconds a step')
    ax.axhline(1.0, color=MUTED, lw=1.0, ls='--')
    ax.text(1200, 1.15, 'one hour', fontsize=9.5, color=MUTED)
    ax.axhline(24.0, color=MUTED, lw=1.0, ls=':')
    ax.text(1200, 27.0, 'one day', fontsize=9.5, color=MUTED)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('steps in the run', fontsize=10)
    ax.set_ylabel('hours the run takes (log scale)', fontsize=10)
    ax.set_title('Steps multiplied by the time of one step',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, TL_DOC, 'arithmetic-and-time.svg')


def checkpoint_size() -> None:
    """What a checkpoint holds, and how big it gets."""
    widths = [64, 256, 1024, 4096]
    weights, with_state = [], []
    for w in widths:
        params = 2 * w * w + w + w
        wb = params * BYTES / 1e6
        weights.append(wb)
        with_state.append(3 * wb)
        print(f'[checkpoint] width {w:>5}: {params:>12,} weights, {wb:8.2f} MB of '
              f'weights, {3 * wb:8.2f} MB with the optimiser state')
    big = LAYERS * (WIDTH * WIDTH + WIDTH)
    print(f'[checkpoint] the {LAYERS}-layer network of width {WIDTH} is '
          f'{big:,} weights, {big * BYTES / 1e6:.1f} MB on its own and '
          f'{3 * big * BYTES / 1e6:.1f} MB with the optimiser state')
    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plot_style(ax)
    xs = np.arange(len(widths))
    ax.bar(xs - 0.19, weights, width=0.36, color=LINK_PALE, edgecolor=LINK, lw=1.4,
           label='the weights alone, which is all you need to use the model')
    ax.bar(xs + 0.19, with_state, width=0.36, color='#f6e3c0', edgecolor=JOINT, lw=1.4,
           label='the weights plus the optimiser state, which is what lets you carry on')
    fmt = lambda v: (f'{v:.2f} MB' if v < 1 else f'{v:.1f} MB')
    for x, v in zip(xs - 0.19, weights):
        ax.text(x, v * 1.3, fmt(v), ha='center', fontsize=9.5, color=INK)
    for x, v in zip(xs + 0.19, with_state):
        ax.text(x, v * 1.3, fmt(v), ha='center', fontsize=9.5, color=INK)
    ax.set_yscale('log')
    ax.set_ylim(0.03, 1e4)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'width {w}' for w in widths], fontsize=10.5)
    ax.set_ylabel('file size in megabytes (log scale)', fontsize=10)
    ax.set_title('A checkpoint you can carry on from is three times the size of one you '
                 'can only use', fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    _save(fig, TL_DOC, 'checkpoint-size.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    np.seterr(all='ignore')          # some runs are meant to blow up
    chain_two_stages()
    chain_curved_stages()
    chain_finite_difference()
    tiny_network_forward()
    forward_arithmetic()
    loss_at_this_prediction()
    tiny_network_backward()
    blame_bars()
    relu_gate()
    one_step()
    the_tape()
    gradient_check()
    activation_memory()
    memory_vs_batch()
    multiplying_many_numbers()
    sigmoid_slope()
    gradient_by_layer()
    residual_gradient()
    normalisation_rescue()
    activation_slopes()
    clipping_run()
    loop_order()
    batches_and_epochs()
    loss_per_step()
    forgetting_to_zero()
    momentum_path()
    momentum_loss()
    momentum_average()
    adam_paths()
    adam_inside()
    adamw_decay()
    schedule_curves()
    schedule_loss()
    warmup_blowup()
    init_zero()
    init_scales()
    init_loss()
    training_curve()
    curve_shapes()
    step_time()
    checkpoint_size()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
