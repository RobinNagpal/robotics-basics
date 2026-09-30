"""Generate the diagrams for the second half of the planning-and-search chapter.

The documents are in docs/05_programming-techniques/06_planning-and-search/:
04_trajectory-optimisation.md and 05_numerical-inverse-kinematics.md. Each
picture illustrates one idea from its own document, and goes to
docs/images/planning-and-search/<doc-name>/.

Run with:  pixi run python ../docs/diagrams/planning_and_search_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every picture here shows the result of a real run. The script runs gradient
descent on a path around a round obstacle, and damped least squares inverse
kinematics on the two-link arm from Book 1 (links 3 m and 2 m). It also prints
the numbers the two documents quote, so they can be checked against this run.
"""

import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'planning-and-search')
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

# The same palette as the other diagram scripts.
GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
WRIST: str = '#e07b39'
INK: str = '#222222'
MUTED: str = '#777777'
OBSTACLE: str = '#9a9a9a'
OBSTACLE_PALE: str = '#e4e4e4'
PURPLE: str = '#7b5aa6'

Point = tuple[float, float]
Array = NDArray[np.float64]

TRAJ: str = 'trajectory-optimisation'
IK: str = 'numerical-inverse-kinematics'


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
           ha: str = 'center', weight: str = 'normal') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            zorder=9)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _arrow(ax: Axes, a: Point, b: Point, color: str = INK, lw: float = 2.0) -> None:
    ax.annotate('', xy=b, xytext=a, arrowprops={'arrowstyle': '-|>', 'color': color,
                                                'lw': lw, 'shrinkA': 0, 'shrinkB': 0,
                                                'mutation_scale': 16},
                zorder=8)


def _chart(ax: Axes) -> None:
    ax.set_facecolor('white')
    ax.grid(True, color=GRID, lw=0.8, zorder=1)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9.5)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------
# trajectory optimisation: the path, the cost and gradient descent
# --------------------------------------------------------------------------
#
# The path is 21 waypoints from (0, 0) to (10, 0). One unit is 10 cm. The two
# ends are fixed. The cost has two parts, in the CHOMP style:
#   smoothness = sum over neighbours of the squared distance between them
#   obstacle   = sum over waypoints of a penalty that is zero beyond the margin,
#                grows gently inside the margin and steeply inside the obstacle
# total = smoothness + WEIGHT * obstacle. Each step moves every inner waypoint a
# little against the gradient of the total.

N_WAYPOINTS: int = 21
START: Array = np.array([0.0, 0.0])
GOAL: Array = np.array([10.0, 0.0])
MARGIN: float = 0.5          # the clearance the path should keep, 5 cm
WEIGHT: float = 10.0         # how much the obstacle cost counts against smoothness
STEP: float = 0.05           # the step size of gradient descent
ITERATIONS: int = 300
POT_CENTRE: Array = np.array([5.0, 0.4])   # a round pot, a little off the line
POT_RADIUS: float = 1.5

Obstacle = tuple[Array, float]


def _obstacle_cost(p: Array, obstacle: Obstacle) -> tuple[float, Array]:
    """The penalty for one waypoint and its gradient, from its distance to the surface."""
    centre, radius = obstacle
    v = p - centre
    dist = float(np.linalg.norm(v))
    d = dist - radius                                  # signed distance to the surface
    away = v / dist if dist > 1e-12 else np.zeros(2)   # no direction at the exact centre
    if d < 0:
        return -d + MARGIN / 2, -away
    if d < MARGIN:
        return (d - MARGIN) ** 2 / (2 * MARGIN), (d - MARGIN) / MARGIN * away
    return 0.0, np.zeros(2)


def _path_cost(path: Array, obstacles: list[Obstacle]) -> tuple[float, float, Array, Array]:
    """Smoothness cost, obstacle cost, and the gradient of each, for every waypoint."""
    smooth = float(np.sum(np.diff(path, axis=0) ** 2))
    g_smooth = np.zeros_like(path)
    g_smooth[1:-1] = 2 * (2 * path[1:-1] - path[:-2] - path[2:])
    obst = 0.0
    g_obst = np.zeros_like(path)
    for i in range(1, len(path) - 1):
        for ob in obstacles:
            c, g = _obstacle_cost(path[i], ob)
            obst += c
            g_obst[i] += g
    return smooth, obst, g_smooth, g_obst


def _clearance(path: Array, obstacles: list[Obstacle], samples: int = 50) -> float:
    """The smallest distance from the obstacle surface, checked along every segment."""
    best = math.inf
    for a, b in zip(path[:-1], path[1:]):
        for s in np.linspace(0, 1, samples):
            p = a * (1 - s) + b * s
            for centre, radius in obstacles:
                best = min(best, float(np.linalg.norm(p - centre)) - radius)
    return best


def _length(path: Array) -> float:
    return float(np.sum(np.linalg.norm(np.diff(path, axis=0), axis=1)))


def optimise_path(obstacles: list[Obstacle], first: Array | None = None,
                  iterations: int = ITERATIONS) -> tuple[list[Array], list[tuple[float, float]]]:
    """Gradient descent on the whole path. Returns every path and every (smooth, obstacle)."""
    path = np.linspace(START, GOAL, N_WAYPOINTS) if first is None else first.copy()
    paths = [path.copy()]
    costs: list[tuple[float, float]] = []
    for k in range(iterations + 1):
        smooth, obst, g_s, g_o = _path_cost(path, obstacles)
        costs.append((smooth, obst))
        if k == iterations:
            break
        path[1:-1] -= STEP * (g_s[1:-1] + WEIGHT * g_o[1:-1])
        paths.append(path.copy())
    return paths, costs


def _pot(ax: Axes, centre: Array, radius: float, label: bool = True) -> None:
    ax.add_patch(Circle(tuple(centre), radius + MARGIN, facecolor='none', edgecolor=OBSTACLE,
                        lw=1.2, ls=(0, (4, 3)), zorder=1))
    ax.add_patch(Circle(tuple(centre), radius, facecolor=OBSTACLE_PALE, edgecolor=OBSTACLE,
                        lw=1.5, zorder=2))
    if label:
        _label(ax, centre[0], centre[1], 'pot', 10, MUTED)


def _ends(ax: Axes) -> None:
    ax.plot([START[0]], [START[1]], 'o', color=INK, ms=9, zorder=7)
    ax.plot([GOAL[0]], [GOAL[1]], '*', color=GRIP, ms=17, zorder=7)
    _label(ax, START[0], START[1] - 0.55, 'start', 10)
    _label(ax, GOAL[0], GOAL[1] - 0.6, 'goal', 10)


def straight_to_smooth(paths: list[Array]) -> None:
    """The straight first guess through the pot, and the paths gradient descent makes."""
    obstacles = [(POT_CENTRE, POT_RADIUS)]
    fig, ax = plt.subplots(figsize=(10, 5.4), facecolor='white')
    _axes(ax, (-0.8, 10.8), (-2.4, 2.9))
    _pot(ax, POT_CENTRE, POT_RADIUS)
    first = paths[0]
    ax.plot(first[:, 0], first[:, 1], color=MUTED, lw=1.5, ls=(0, (5, 3)), zorder=3)
    ax.plot(first[1:-1, 0], first[1:-1, 1], 'o', color=MUTED, ms=4, zorder=3)
    for k, shade in ((1, '#dfe9f4'), (3, '#c9dcef'), (10, '#9dbfe0')):
        p = paths[k]
        ax.plot(p[:, 0], p[:, 1], color=shade, lw=2, zorder=4)
    last = paths[-1]
    ax.plot(last[:, 0], last[:, 1], color=LINK, lw=2.6, zorder=5)
    ax.plot(last[1:-1, 0], last[1:-1, 1], 'o', color=LINK, ms=5, zorder=6)
    _ends(ax)
    _label(ax, 0.2, 0.45, 'first guess: a straight line', 10, MUTED, ha='left')
    _label(ax, 7.0, -1.3, f'after {len(paths) - 1} steps', 10.5, LINK, ha='left',
           weight='bold')
    _label(ax, 6.9, 2.05, 'dashed ring: the 5 cm margin', 9.5, MUTED, ha='left')
    _label(ax, 1.2, -1.75, 'pale lines: after 1, 3\nand 10 steps', 9.5, LINK, ha='left')
    c0 = _clearance(first, obstacles)
    c1 = _clearance(last, obstacles)
    _title(ax, 5.0, 2.65, f'Clearance from the pot: {c0 * 10:.1f} cm at the start, '
                          f'{c1 * 10:.1f} cm at the end', 11.5)
    _save(fig, TRAJ, 'straight-to-smooth.svg')


def two_pushes(paths: list[Array]) -> None:
    """The two parts of the step on one waypoint: a pull from its neighbours, a push out."""
    obstacles = [(POT_CENTRE, POT_RADIUS)]
    k = 3
    path = paths[k]
    _, _, g_s, g_o = _path_cost(path, obstacles)
    i = 9
    p = path[i]
    pull = -STEP * g_s[i]
    push = -STEP * WEIGHT * g_o[i]
    both = pull + push
    scale = 8.0     # the arrows are drawn eight times their real length so they can be seen
    fig, ax = plt.subplots(figsize=(9, 6.4), facecolor='white')
    _axes(ax, (1.9, 6.6), (-2.2, 2.5))
    _pot(ax, POT_CENTRE, POT_RADIUS, label=False)
    _label(ax, 5.0, 0.6, 'pot', 10, MUTED)
    ax.plot(path[:, 0], path[:, 1], color=LINK_PALE, lw=2.2, zorder=3)
    ax.plot(path[1:-1, 0], path[1:-1, 1], 'o', color=LINK_PALE, ms=6, zorder=4)
    for j in (i - 1, i + 1):
        ax.plot([path[j, 0]], [path[j, 1]], 'o', color=LINK, ms=8, zorder=6)
    mid = (path[i - 1] + path[i + 1]) / 2
    ax.plot([mid[0]], [mid[1]], 'x', color=SLIDE, ms=10, mew=2.2, zorder=6)
    ax.plot([p[0]], [p[1]], 'o', color=INK, ms=10, zorder=7)
    _arrow(ax, tuple(p), tuple(p + scale * pull), SLIDE)
    _arrow(ax, tuple(p), tuple(p + scale * push), GRIP)
    _arrow(ax, tuple(p), tuple(p + scale * both), PURPLE, lw=2.6)
    tip_push = p + scale * push
    _label(ax, mid[0] + 0.1, mid[1] + 0.45, 'smoothness: towards\nthe middle of its\nneighbours (the x)',
           9.5, SLIDE, ha='left')
    _label(ax, tip_push[0] - 0.05, tip_push[1] - 0.35, 'obstacle: straight\naway from the pot',
           9.5, GRIP, ha='right')
    _label(ax, 3.3, -1.95, 'purple: the step it takes',
           10, PURPLE, ha='left', weight='bold')
    _label(ax, p[0] - 0.2, p[1] + 0.02, f'waypoint {i}', 9.5, INK, ha='right')
    _label(ax, path[i - 1][0] - 0.15, path[i - 1][1], 'neighbour', 9, LINK, ha='right')
    _label(ax, path[i + 1][0] + 0.15, path[i + 1][1] - 0.2, 'neighbour', 9, LINK, ha='left')
    _title(ax, 4.25, 2.75, f'One waypoint after {k} steps, arrows drawn {scale:.0f} times longer',
           11.5)
    _save(fig, TRAJ, 'two-pushes.svg')
    print(f'two-pushes: step {k}, waypoint {i} at ({p[0]:.3f}, {p[1]:.3f}), smoothness step '
          f'({pull[0]:.3f}, {pull[1]:.3f}), obstacle step ({push[0]:.3f}, {push[1]:.3f}), '
          f'sum ({both[0]:.3f}, {both[1]:.3f})')


def cost_per_step(paths: list[Array], costs: list[tuple[float, float]]) -> None:
    """The two costs and the clearance, step by step."""
    obstacles = [(POT_CENTRE, POT_RADIUS)]
    steps = np.arange(len(costs))
    smooth = np.array([c[0] for c in costs])
    obst = np.array([WEIGHT * c[1] for c in costs])
    clear = np.array([_clearance(p, obstacles) * 10 for p in paths])
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2), facecolor='white')
    _chart(a)
    a.plot(steps, smooth + obst, color=INK, lw=2.4, zorder=4, label='total')
    a.plot(steps, smooth, color=SLIDE, lw=2, zorder=3, label='smoothness')
    a.plot(steps, obst, color=GRIP, lw=2, zorder=3, label=f'obstacle x {WEIGHT:.0f}')
    a.set_xscale('symlog', linthresh=10)
    a.set_xlim(0, ITERATIONS)
    a.set_ylim(0, 62)
    a.set_xticks([0, 1, 5, 10, 50, 100, 300])
    a.set_xticklabels(['0', '1', '5', '10', '50', '100', '300'])
    a.set_xlabel('step', fontsize=10, color=INK)
    a.set_ylabel('cost', fontsize=10, color=INK)
    a.legend(frameon=False, fontsize=9.5, loc='upper right')
    a.set_title('The cost falls fast, then slowly', fontsize=11.5, color=INK, weight='bold')
    _chart(b)
    b.axhspan(-12, 0, color='#fbe3e3', zorder=0)
    b.plot(steps, clear, color=LINK, lw=2.4, zorder=4)
    b.axhline(MARGIN * 10, color=MUTED, lw=1.2, ls=(0, (4, 3)), zorder=3)
    b.set_xscale('symlog', linthresh=10)
    b.set_xlim(0, ITERATIONS)
    b.set_ylim(-12, 7)
    b.set_xticks([0, 1, 5, 10, 50, 100, 300])
    b.set_xticklabels(['0', '1', '5', '10', '50', '100', '300'])
    b.set_xlabel('step', fontsize=10, color=INK)
    b.set_ylabel('clearance from the pot, cm', fontsize=10, color=INK)
    b.text(20, -9.5, 'inside the pot', fontsize=9.5, color=GRIP, ha='left', va='center')
    b.text(0.4, 5.8, 'the 5 cm margin', fontsize=9.5, color=MUTED, ha='left', va='center')
    b.set_title('The path is clear of the pot after 3 steps', fontsize=11.5, color=INK,
                weight='bold')
    fig.tight_layout(w_pad=3)
    _save(fig, TRAJ, 'cost-per-step.svg')
    first_clear = next(k for k, c in enumerate(clear) if c > 0)
    print(f'cost-per-step: path first clear of the pot at step {first_clear}')


def stuck_in_the_middle() -> tuple[list[Array], list[Array]]:
    """A pot centred on the line: the pushes cancel. A 5 mm nudge breaks the tie."""
    centred: list[Obstacle] = [(np.array([5.0, 0.0]), POT_RADIUS)]
    stuck, _ = optimise_path(centred)
    nudge = np.linspace(START, GOAL, N_WAYPOINTS)
    nudge[N_WAYPOINTS // 2, 1] += 0.05
    freed, _ = optimise_path(centred, first=nudge)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), facecolor='white')
    for ax, run, title in ((axes[0], stuck, 'Exactly on the line: stuck'),
                           (axes[1], freed, 'Nudged 5 mm up: it goes round')):
        _axes(ax, (-0.8, 10.8), (-2.6, 3.4))
        _pot(ax, centred[0][0], POT_RADIUS, label=False)
        _label(ax, 5.0, -0.8, 'pot', 10, MUTED)
        last = run[-1]
        color = GRIP if ax is axes[0] else LINK
        ax.plot(last[:, 0], last[:, 1], color=color, lw=2.4, zorder=5)
        ax.plot(last[1:-1, 0], last[1:-1, 1], 'o', color=color, ms=5, zorder=6)
        _ends(ax)
        _title(ax, 5.0, 3.15, title, 11.5)
        c = _clearance(last, centred)
        _label(ax, 5.0, -2.35, f'clearance after {len(run) - 1} steps: {c * 10:.1f} cm', 10,
               color)
    _label(axes[0], 8.2, 2.1, 'one waypoint\nleft at the centre', 9.5, GRIP)
    _arrow(axes[0], (7.4, 1.8), (5.15, 0.15), GRIP, 1.4)
    _save(fig, TRAJ, 'stuck-in-the-middle.svg')
    return stuck, freed


def trajectory_numbers(paths: list[Array], costs: list[tuple[float, float]],
                       stuck: list[Array], freed: list[Array]) -> None:
    obstacles = [(POT_CENTRE, POT_RADIUS)]
    print('trajectory optimisation: step, smoothness, obstacle, total, clearance cm, '
          'length cm')
    for k in (0, 1, 5, 10, 50, 100, 300):
        s, o = costs[k]
        print(f'  {k:4d} {s:8.3f} {o:8.3f} {s + WEIGHT * o:8.3f} '
              f'{_clearance(paths[k], obstacles) * 10:7.2f} {_length(paths[k]) * 10:7.1f}')
    print('  furthest waypoint from the line after the last step: '
          f'{np.abs(paths[-1][:, 1]).max() * 10:.1f} cm')
    centred = [(np.array([5.0, 0.0]), POT_RADIUS)]
    print(f'  centred pot: clearance {_clearance(stuck[-1], centred) * 10:.1f} cm, '
          f'total cost {sum(_path_cost(stuck[-1], centred)[:1]) + WEIGHT * _path_cost(stuck[-1], centred)[1]:.3f}')
    print(f'  nudged: clearance {_clearance(freed[-1], centred) * 10:.1f} cm')
    for k in (0, 1, 2, 5, 10):
        print(f'    nudged step {k}: middle waypoint y = {freed[k][N_WAYPOINTS // 2, 1] * 10:.1f} cm,'
              f' clearance {_clearance(freed[k], centred) * 10:.1f} cm')


# --------------------------------------------------------------------------
# numerical inverse kinematics: the two-link arm from Book 1
# --------------------------------------------------------------------------

L1: float = 3.0
L2: float = 2.0
TARGET: Array = np.array([3 * math.cos(math.radians(30)), 3.5])  # (2.598, 3.5), from 30 and 60
TOO_FAR: Array = np.array([6.0, 0.0])


def fk(q: Array) -> Array:
    return np.array([L1 * math.cos(q[0]) + L2 * math.cos(q[0] + q[1]),
                     L1 * math.sin(q[0]) + L2 * math.sin(q[0] + q[1])])


def jacobian(q: Array) -> Array:
    s1, c1 = math.sin(q[0]), math.cos(q[0])
    s12, c12 = math.sin(q[0] + q[1]), math.cos(q[0] + q[1])
    return np.array([[-L1 * s1 - L2 * s12, -L2 * s12],
                     [L1 * c1 + L2 * c12, L2 * c12]])


def ik_step(q: Array, target: Array, method: str, damping: float = 1.0) -> Array:
    """One correction. 'dls' is damped least squares, 'pinv' the plain pseudo-inverse,
    'transpose' the Jacobian transpose (gradient descent on the squared miss)."""
    miss = target - fk(q)
    j = jacobian(q)
    if method == 'dls':
        return j.T @ np.linalg.solve(j @ j.T + damping ** 2 * np.eye(2), miss)
    if method == 'pinv':
        return np.linalg.pinv(j) @ miss
    return 0.05 * j.T @ miss


def solve_ik(start_deg: tuple[float, float], target: Array, method: str,
             damping: float = 1.0, steps: int = 100,
             tol: float = 1e-6) -> list[tuple[Array, float]]:
    q = np.radians(np.array(start_deg, dtype=float))
    out = [(q.copy(), float(np.linalg.norm(target - fk(q))))]
    for _ in range(steps):
        q = q + ik_step(q, target, method, damping)
        miss = float(np.linalg.norm(target - fk(q)))
        out.append((q.copy(), miss))
        if miss < tol:
            break
    return out


def solve_lm(start_deg: tuple[float, float], target: Array, damping: float = 1.0,
             tol: float = 1e-6) -> list[tuple[Array, float, float]]:
    """Damped least squares with the damping changed as it goes (Levenberg-Marquardt):
    halve it after a step that shrinks the miss, double it and retry after one that does not.
    Stop when the miss is below tol, or when the damping has grown past 1000."""
    q = np.radians(np.array(start_deg, dtype=float))
    miss = float(np.linalg.norm(target - fk(q)))
    out = [(q.copy(), miss, damping)]
    while miss >= tol and damping <= 1000:
        dq = ik_step(q, target, 'dls', damping)
        new = float(np.linalg.norm(target - fk(q + dq)))
        if new < miss - 1e-12:
            q = q + dq
            miss = new
            damping = max(damping / 2, 1e-3)
            out.append((q.copy(), miss, damping))
        else:
            damping *= 2
    return out


def _arm(ax: Axes, q: Array, color: str = LINK, width: float = 6, z: int = 3,
         joints: bool = True) -> Array:
    elbow = np.array([L1 * math.cos(q[0]), L1 * math.sin(q[0])])
    tip = fk(q)
    ax.plot([0, elbow[0], tip[0]], [0, elbow[1], tip[1]], color=color, lw=width,
            solid_capstyle='round', zorder=z)
    if joints:
        ax.plot([0, elbow[0]], [0, elbow[1]], 'o', color=JOINT, ms=8, zorder=z + 1)
    return tip


def _base(ax: Axes) -> None:
    ax.plot([-0.6, 0.6], [-0.18, -0.18], color=MUTED, lw=1.4, zorder=1)
    for x in np.linspace(-0.55, 0.55, 6):
        ax.plot([x, x - 0.15], [-0.18, -0.33], color=GRID, lw=1, zorder=1)


def dls_steps(run: list[tuple[Array, float]]) -> None:
    """The arm at every step of damped least squares, from (0, 30) to the target."""
    fig, ax = plt.subplots(figsize=(8.4, 6.0), facecolor='white')
    _axes(ax, (-1.2, 6.8), (-0.6, 4.7))
    _base(ax)
    shades = ['#e3ecf6', '#d2e1f1', '#bcd3eb', '#a2c1e2', '#86aed8', '#6a9bce']
    tips = []
    for k, (q, _) in enumerate(run[:-1]):
        color = shades[min(k, len(shades) - 1)]
        tips.append(_arm(ax, q, color, 4, z=2 + k // 4, joints=False))
    tips.append(_arm(ax, run[-1][0], LINK, 6, z=6))
    tips_arr = np.array(tips)
    ax.plot(tips_arr[:, 0], tips_arr[:, 1], color=PURPLE, lw=1.2, ls=(0, (3, 2)), zorder=7)
    ax.plot(tips_arr[:, 0], tips_arr[:, 1], 'o', color=PURPLE, ms=4, zorder=8)
    ax.plot([TARGET[0]], [TARGET[1]], '*', color=GRIP, ms=20, zorder=9)
    for k in (0, 1):
        _, miss = run[k]
        t = tips[k]
        _label(ax, t[0] + 0.25, t[1], f'step {k}: miss {miss:.2f} m', 9.5, PURPLE, ha='left')
    _label(ax, TARGET[0] + 0.35, TARGET[1] + 0.3,
           f'target (2.598, 3.5)', 9.5, GRIP, ha='left')
    _label(ax, TARGET[0] + 0.35, TARGET[1] - 0.2,
           f'steps 2 to {len(run) - 1} close the last {run[2][1] * 100:.0f} cm', 9.5, PURPLE,
           ha='left')
    _title(ax, 2.5, 4.5, 'Damped least squares, damping 1.0, from (0°, 30°)', 11.5)
    _save(fig, IK, 'dls-steps.svg')


def jacobian_columns() -> None:
    """The two columns of the Jacobian drawn at the gripper: normal pose and nearly straight."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), facecolor='white')
    cases = ((np.radians([30.0, 60.0]), 'Elbow at 60°: two different directions'),
             (np.radians([20.0, 5.0]), 'Elbow at 5°: both point almost the same way'))
    for ax, (q, title) in zip(axes, cases):
        _axes(ax, (-0.9, 6.4), (-0.8, 5.4))
        _base(ax)
        tip = _arm(ax, q)
        j = jacobian(q)
        scale = 0.35
        for col, color, name in ((0, GRIP, 'turn joint 1'), (1, SLIDE, 'turn joint 2')):
            v = j[:, col] * scale
            _arrow(ax, tuple(tip), tuple(tip + v), color, 2.4)
            end = tip + v
            _label(ax, end[0] + (0.1 if v[0] >= 0 else -0.1), end[1] + 0.22,
                   f'{name}\n({j[0, col]:.2f}, {j[1, col]:.2f}) m per rad', 9,
                   color, ha='left' if v[0] >= 0 else 'right')
        det = float(np.linalg.det(j))
        _title(ax, 2.8, 5.15, title, 11.5)
        _label(ax, 2.8, -0.6, f'determinant = 6 · sin(q2) = {det:.2f}', 10, INK)
    _save(fig, IK, 'jacobian-columns.svg')


def step_near_singularity() -> list[tuple[float, float, float, float]]:
    """The joint step each method asks for, to pull the gripper 10 cm towards the base."""
    elbows = np.array([30, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1])
    rows = []
    for e in elbows:
        q = np.radians([0.0, e])
        j = jacobian(q)
        miss = np.array([-0.1, 0.0])
        inv = math.degrees(float(np.linalg.norm(np.linalg.solve(j, miss))))
        d05 = math.degrees(float(np.linalg.norm(j.T @ np.linalg.solve(j @ j.T + 0.25 * np.eye(2), miss))))
        d10 = math.degrees(float(np.linalg.norm(j.T @ np.linalg.solve(j @ j.T + np.eye(2), miss))))
        rows.append((float(e), inv, d05, d10))
    arr = np.array(rows)
    fig, ax = plt.subplots(figsize=(8.6, 4.8), facecolor='white')
    _chart(ax)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.plot(arr[:, 0], arr[:, 1], 'o-', color=GRIP, lw=2.2, ms=5, zorder=4,
            label='plain inverse')
    ax.plot(arr[:, 0], arr[:, 2], 'o-', color=WRIST, lw=2.2, ms=5, zorder=4,
            label='damped, damping 0.5')
    ax.plot(arr[:, 0], arr[:, 3], 'o-', color=LINK, lw=2.2, ms=5, zorder=4,
            label='damped, damping 1.0')
    ax.axhline(30, color=MUTED, lw=1.2, ls=(0, (4, 3)), zorder=3)
    ax.text(0.12, 38, '30°, the step limit in Book 1', fontsize=9, color=MUTED, ha='right')
    ax.invert_xaxis()
    ax.set_xlabel('elbow angle q2, degrees (the arm straightens to the right)', fontsize=10,
                  color=INK)
    ax.set_ylabel('size of the joint step, degrees', fontsize=10, color=INK)
    ax.set_xticks([30, 10, 3, 1, 0.3, 0.1])
    ax.set_xticklabels(['30', '10', '3', '1', '0.3', '0.1'])
    ax.legend(frameon=False, fontsize=9.5, loc='upper left')
    ax.set_title('The step asked for to move the gripper 10 cm towards the base',
                 fontsize=11.5, color=INK, weight='bold')
    _save(fig, IK, 'step-near-singularity.svg')
    return rows


def miss_per_step() -> None:
    """The miss at each step for three methods, on the reachable target and on (6, 0)."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.6), facecolor='white')
    runs = (('pseudo-inverse, no step limit', 'pinv', GRIP, 1.0),
            ('damped, damping 1.0', 'dls', LINK, 1.0),
            ('Jacobian transpose', 'transpose', SLIDE, 1.0))
    _chart(a)
    for name, method, color, d in runs:
        r = solve_ik((0, 30), TARGET, method, d, steps=40)
        a.plot(range(len(r)), [max(m, 1e-9) for _, m in r], 'o-', color=color, lw=2, ms=3.5,
               label=name, zorder=4)
    a.set_yscale('log')
    a.set_ylim(1e-8, 20)
    a.set_xlim(0, 40)
    a.set_xlabel('step', fontsize=10, color=INK)
    a.set_ylabel('miss, metres', fontsize=10, color=INK)
    a.legend(frameon=False, fontsize=9.5, loc='lower left')
    a.set_title('Target (2.598, 3.5): all three get closer', fontsize=11.5, color=INK,
                weight='bold')
    _chart(b)
    for name, method, color, d in runs[:2]:
        r = solve_ik((10, 20), TOO_FAR, method, d, steps=40, tol=0)
        b.plot(range(len(r)), [m for _, m in r], 'o-', color=color, lw=2, ms=3.5, label=name,
               zorder=4)
    b.axhline(1.0, color=MUTED, lw=1.2, ls=(0, (4, 3)), zorder=3)
    b.text(39, 0.45, '1 m: as close as a 5 m arm can get', fontsize=9, color=MUTED, ha='right')
    b.set_xlim(0, 40)
    b.set_ylim(0, 14)
    b.set_xlabel('step', fontsize=10, color=INK)
    b.set_ylabel('miss, metres', fontsize=10, color=INK)
    b.legend(frameon=False, fontsize=9.5, loc='upper right')
    b.set_title('Target (6, 0), out of reach', fontsize=11.5, color=INK, weight='bold')
    fig.tight_layout(w_pad=3)
    _save(fig, IK, 'miss-per-step.svg')


def ik_numbers(rows: list[tuple[float, float, float, float]]) -> None:
    print('numerical IK, damped least squares, damping 1.0, from (0, 30):')
    for k, (q, m) in enumerate(solve_ik((0, 30), TARGET, 'dls', 1.0)):
        print(f'  step {k:2d}: q1 = {math.degrees(q[0]):7.2f}, q2 = {math.degrees(q[1]):7.2f}, '
              f'miss = {m:.6f} m')
    print('plain pseudo-inverse, no step limit, from (0, 30):')
    for k, (q, m) in enumerate(solve_ik((0, 30), TARGET, 'pinv')):
        print(f'  step {k:2d}: q1 = {math.degrees(q[0]):7.2f}, q2 = {math.degrees(q[1]):7.2f}, '
              f'miss = {m:.6f} m')
    r = solve_ik((0, 30), TARGET, 'transpose')
    print(f'Jacobian transpose: miss after {len(r) - 1} steps = {r[-1][1]:.6f} m')
    q = np.radians([30.0, 60.0])
    print('Jacobian at (30, 60):', jacobian(q).round(3).tolist(),
          f'determinant {np.linalg.det(jacobian(q)):.3f}')
    q = np.radians([20.0, 5.0])
    print('Jacobian at (20, 5):', jacobian(q).round(3).tolist(),
          f'determinant {np.linalg.det(jacobian(q)):.3f}')
    print('step to move 10 cm towards the base, q1 = 0: elbow, inverse, dls 0.5, dls 1.0 (deg)')
    for e, inv, d05, d10 in rows:
        print(f'  {e:5.1f} {inv:9.1f} {d05:7.2f} {d10:7.2f}')
    print('damping sweep: steps to reach (2.598, 3.5) from (0, 30); then (6, 0) from (10, 20)')
    for d in (0.05, 0.2, 0.5, 1.0, 2.0):
        a = solve_ik((0, 30), TARGET, 'dls', d, steps=500)
        b = solve_ik((10, 20), TOO_FAR, 'dls', d, steps=100, tol=0)
        last = [round(m, 3) for _, m in b[-4:]]
        print(f'  damping {d:4.2f}: {len(a) - 1:3d} steps, first step '
              f'{np.degrees(np.abs(a[1][0] - a[0][0])).round(1).tolist()}; out of reach, last '
              f'misses {last}, final pose {np.degrees(b[-1][0]).round(2).tolist()}')
    b = solve_ik((10, 20), TOO_FAR, 'pinv', steps=100, tol=0)
    print(f'  plain pinv out of reach: final miss {b[-1][1]:.3f}, pose '
          f'{np.degrees(b[-1][0]).round(1).tolist()}')
    for target, start in ((TARGET, (0.0, 30.0)), (TOO_FAR, (10.0, 20.0))):
        r = solve_lm(start, target)
        print(f'Levenberg-Marquardt to {target.round(3).tolist()}: {len(r) - 1} accepted steps, '
              f'final miss {r[-1][1]:.6f}, pose {np.degrees(r[-1][0]).round(2).tolist()}')
    near = np.array([4.9, 0.0])
    print('from nearly straight (0, 0.1) to (4.9, 0), 10 cm towards the base; '
          f'the answer needs q2 = {math.degrees(math.acos((4.9 ** 2 - 13) / 12)):.2f}:')
    for name, method, d in (('pinv', 'pinv', 1.0), ('dls 0.5', 'dls', 0.5),
                            ('dls 1.0', 'dls', 1.0)):
        r = solve_ik((0.0, 0.1), near, method, d, steps=200)
        worst = max(float(np.degrees(np.abs(r[k + 1][0] - r[k][0])).max())
                    for k in range(len(r) - 1))
        print(f'  {name}: {len(r) - 1} steps, largest single joint step {worst:.1f} deg, '
              f'final pose {np.degrees(r[-1][0]).round(2).tolist()}')
    r = solve_lm((0.0, 0.1), near)
    print(f'  Levenberg-Marquardt: {len(r) - 1} accepted steps, final pose '
          f'{np.degrees(r[-1][0]).round(2).tolist()}')
    print('three joints (3, 2, 1 m), target (3.464, 4), damping 0.5:')
    lengths = (3.0, 2.0, 1.0)

    def fk3(q: Array) -> Array:
        a = np.cumsum(q)
        return np.array([sum(lengths[i] * math.cos(a[i]) for i in range(3)),
                         sum(lengths[i] * math.sin(a[i]) for i in range(3))])

    def jac3(q: Array) -> Array:
        a = np.cumsum(q)
        j = np.zeros((2, 3))
        for c in range(3):
            j[0, c] = -sum(lengths[i] * math.sin(a[i]) for i in range(c, 3))
            j[1, c] = sum(lengths[i] * math.cos(a[i]) for i in range(c, 3))
        return j

    t3 = np.array([3.464101615, 4.0])
    for start in ((0.0, 30.0, 0.0), (90.0, -30.0, 0.0)):
        q = np.radians(np.array(start))
        k = 0
        while np.linalg.norm(t3 - fk3(q)) >= 1e-6 and k < 200:
            j = jac3(q)
            q = q + j.T @ np.linalg.solve(j @ j.T + 0.25 * np.eye(2), t3 - fk3(q))
            k += 1
        print(f'  from {start}: {np.degrees(q).round(2).tolist()} in {k} steps, gripper angle '
              f'{math.degrees(q.sum()):.2f}')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    paths, costs = optimise_path([(POT_CENTRE, POT_RADIUS)])
    straight_to_smooth(paths)
    two_pushes(paths)
    cost_per_step(paths, costs)
    stuck, freed = stuck_in_the_middle()
    trajectory_numbers(paths, costs, stuck, freed)
    run = solve_ik((0, 30), TARGET, 'dls', 1.0)
    dls_steps(run)
    jacobian_columns()
    rows = step_near_singularity()
    miss_per_step()
    ik_numbers(rows)
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
