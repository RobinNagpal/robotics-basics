"""Generate the diagrams for the second half of docs/06_programming-techniques/08_decisions-and-task-logic/.

This covers 04_greedy-algorithms-and-set-cover and 05_optimisation-solvers. Each
document's pictures go to a folder named after it, under
docs/images/decisions-and-task-logic/.

Run with:  pixi run python ../docs/diagrams/decisions_2.py
Add --png <dir> to also write PNG copies for checking.

Every result drawn here is computed in this script, not typed in. The greedy set
cover and the brute-force optimum are both run on the drawn scene. The random
trials are run with a fixed seed. The assignment, the pick order and the packing
problem are all solved exactly by trying every possibility. Run the script and
it prints the numbers the documents quote.
"""

import itertools
import math
import pathlib
import random
import sys
from collections import Counter

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'decisions-and-task-logic')
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

WALL: str = '#f3f3f3'
TABLE: str = '#eadfcb'
PURPLE: str = '#8e5bb5'

# The repository's camera: focal length 277.1 pixels, a 320 by 240 picture.
FX: float = 277.1

# The table, seen from above, in millimetres. x runs left to right along the
# front edge, y runs from the front edge (y = 0, nearest the arm) to the back.
TABLE_W: float = 600.0
TABLE_D: float = 400.0


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _panels(n: int, size: tuple[float, float]) -> tuple[Figure, list[Axes]]:
    fig, axes = plt.subplots(1, n, figsize=size, facecolor='white')
    return fig, list(np.atleast_1d(axes))


def _label(ax: Axes, x: float, y: float, text: str, size: float = 10, color: str = INK,
           ha: str = 'center', weight: str = 'normal') -> None:
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            zorder=9)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _table(ax: Axes) -> None:
    ax.add_patch(Rectangle((0, 0), TABLE_W, TABLE_D, facecolor=TABLE, edgecolor=MUTED,
                           lw=1.0, zorder=1))


def _object(ax: Axes, xy: tuple[float, float], name: str, face: str = 'white',
            edge: str = INK, text: str = INK, r: float = 22) -> None:
    ax.add_patch(Circle(xy, r, facecolor=face, edgecolor=edge, lw=1.4, zorder=5))
    _label(ax, xy[0], xy[1], name, size=10, color=text, weight='bold')


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str,
           lw: float = 2.0, shrink: float = 24, rad: float = 0.0) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=14, color=color,
                                 lw=lw, shrinkA=shrink, shrinkB=shrink, zorder=4,
                                 connectionstyle=f'arc3,rad={rad}'))


# ==========================================================================
# 04_greedy-algorithms-and-set-cover
# ==========================================================================

SET_COVER: str = 'greedy-algorithms-and-set-cover'

# Eight glasses on the table, seen from above.
GLASSES: dict[str, tuple[float, float]] = {
    'A': (60, 260), 'B': (170, 130), 'C': (230, 290), 'D': (270, 170),
    'E': (340, 120), 'F': (380, 280), 'G': (440, 180), 'H': (545, 250),
}

# Four candidate camera views, each looking straight down: the point on the
# table under the camera, and the camera's height above the table.
VIEWS: dict[str, tuple[float, float, float]] = {
    'L': (150, 200, 277.1),     # left, 277 mm up
    'M': (300, 200, 277.1),     # middle, 277 mm up
    'R': (450, 200, 277.1),     # right, 277 mm up
    'S': (500, 220, 180.0),     # right, lower and closer
}
VIEW_COLOUR: dict[str, str] = {'L': LINK, 'M': JOINT, 'R': SLIDE, 'S': PURPLE}


def footprint(cx: float, cy: float, h: float) -> tuple[float, float, float, float]:
    """The patch of table a straight-down camera sees: x0, x1, y0, y1 in mm."""
    w: float = h * 320 / FX
    d: float = h * 240 / FX
    return cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2


def seen_by(view: tuple[float, float, float],
            objects: dict[str, tuple[float, float]]) -> set[str]:
    x0, x1, y0, y1 = footprint(*view)
    return {k for k, (x, y) in objects.items() if x0 <= x <= x1 and y0 <= y <= y1}


def greedy_cover(universe: set, sets: dict) -> list[tuple[object, set]] | None:
    """Repeatedly take the set that covers the most items not yet covered."""
    left: set = set(universe)
    picks: list[tuple[object, set]] = []
    while left:
        best = max(sets, key=lambda s: len(sets[s] & left))    # first one wins a tie
        new: set = sets[best] & left
        if not new:
            return None                                         # nothing can cover the rest
        picks.append((best, new))
        left -= new
    return picks


def best_cover(universe: set, sets: dict) -> tuple | None:
    """Try every group of sets, smallest groups first. The first that covers wins."""
    names = list(sets)
    for k in range(1, len(names) + 1):
        for group in itertools.combinations(names, k):
            if set().union(*(sets[n] for n in group)) >= set(universe):
                return group
    return None


SETS: dict[str, set[str]] = {v: seen_by(VIEWS[v], GLASSES) for v in VIEWS}


def _scene(ax: Axes, views: list[str], covered: set[str], new: set[str],
           faded: list[str] | None = None) -> None:
    _axes(ax, (-40, 650), (-30, 440))
    _table(ax)
    for v in faded or []:
        x0, x1, y0, y1 = footprint(*VIEWS[v])
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor='none',
                               edgecolor=VIEW_COLOUR[v], lw=1.2, ls=':', zorder=2))
    for v in views:
        x0, x1, y0, y1 = footprint(*VIEWS[v])
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=VIEW_COLOUR[v],
                               alpha=0.18, edgecolor='none', zorder=2))
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor='none',
                               edgecolor=VIEW_COLOUR[v], lw=2.2, ls='--', zorder=3))
        _label(ax, x0 + 16, y1 + 20, v, size=11, color=VIEW_COLOUR[v], weight='bold')
    for k, xy in GLASSES.items():
        if k in new:
            _object(ax, xy, k, face=GRIP, edge=GRIP, text='white')
        elif k in covered:
            _object(ax, xy, k, face=MUTED, edge=MUTED, text='white')
        else:
            _object(ax, xy, k)


def views_and_footprints() -> None:
    """Each candidate view, and which glasses fall inside the patch it sees."""
    fig, axes = _panels(4, (17, 4.6))
    for ax, v in zip(axes, VIEWS):
        _scene(ax, [v], set(), SETS[v])
        cx, cy, h = VIEWS[v]
        _title(ax, 305, 485, f'View {v}: camera {h:.0f} mm up', size=12)
        _label(ax, 305, -60, 'sees ' + ' '.join(sorted(SETS[v]))
               + f'  ({len(SETS[v])} glasses)', size=11, color=VIEW_COLOUR[v],
               weight='bold')
        ax.set_ylim(-90, 510)
    _save(fig, SET_COVER, 'views-and-footprints.svg')


def greedy_steps() -> None:
    """Greedy takes M first, because it sees the most, and then needs two more."""
    picks = greedy_cover(set(GLASSES), SETS)
    assert picks is not None
    fig, axes = _panels(len(picks), (14, 4.8))
    covered: set[str] = set()
    taken: list[str] = []
    for i, (ax, (v, new)) in enumerate(zip(axes, picks)):
        left_before: set[str] = set(GLASSES) - covered
        gains: str = '   '.join(f'{u}: {len(SETS[u] & left_before)}' for u in VIEWS
                               if u not in taken)
        _scene(ax, [v], covered, new, faded=taken)
        _title(ax, 305, 500, f'Step {i + 1}: take view {v}', size=12)
        _label(ax, 305, 460, 'new glasses each view would add', size=10, color=MUTED)
        _label(ax, 305, 430, gains, size=10, color=INK)
        _label(ax, 305, -60, 'adds ' + ' '.join(sorted(new)), size=11,
               color=GRIP, weight='bold')
        ax.set_ylim(-90, 520)
        covered |= new
        taken.append(v)
    _save(fig, SET_COVER, 'greedy-steps.svg')


def greedy_against_best() -> None:
    """Greedy ends with three views. Trying every group finds two."""
    picks = greedy_cover(set(GLASSES), SETS)
    best = best_cover(set(GLASSES), SETS)
    assert picks is not None and best is not None
    fig, axes = _panels(2, (12, 4.8))
    g_views: list[str] = [v for v, _ in picks]
    _scene(axes[0], g_views, set(), set())
    _title(axes[0], 305, 480, f'Greedy: {len(g_views)} views ({" + ".join(g_views)})')
    _scene(axes[1], list(best), set(), set())
    _title(axes[1], 305, 480, f'Best possible: {len(best)} views ({" + ".join(best)})')
    for ax in axes:
        ax.set_ylim(-40, 510)
    _save(fig, SET_COVER, 'greedy-against-best.svg')


def random_trial(rng: random.Random, n: int, m: int) -> tuple[int, int]:
    """One random scene: n objects, m straight-down views. Returns (greedy, best)."""
    while True:
        objs = {i: (rng.uniform(0, TABLE_W), rng.uniform(0, TABLE_D)) for i in range(n)}
        sets = {j: seen_by((rng.uniform(0, TABLE_W), rng.uniform(0, TABLE_D),
                            rng.uniform(150, 350)), objs) for j in range(m)}
        if set().union(*sets.values()) == set(objs):
            break                                   # keep only scenes that can be covered
    g = greedy_cover(set(objs), sets)
    b = best_cover(set(objs), sets)
    assert g is not None and b is not None
    return len(g), len(b)


def random_trials() -> None:
    """How often greedy finds the smallest set, over 1000 random scenes of each size."""
    rng = random.Random(1)
    sizes: list[tuple[int, int]] = [(8, 8), (12, 12), (20, 16)]
    rows: list[Counter] = []
    print('random set cover trials (objects, views): extra views -> count')
    for n, m in sizes:
        res = [random_trial(rng, n, m) for _ in range(1000)]
        c = Counter(g - b for g, b in res)
        rows.append(c)
        print(f'  {n} objects, {m} views: {dict(sorted(c.items()))}, '
              f'mean best {sum(b for _, b in res) / 1000:.2f}, '
              f'mean greedy {sum(g for g, _ in res) / 1000:.2f}, '
              f'worst ratio {max(g / b for g, b in res):.2f}')
    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor='white')
    width: float = 0.26
    colours: list[str] = [SLIDE, JOINT, GRIP]
    names: list[str] = ['same as the best', 'one view more', 'two views more']
    x = np.arange(len(sizes))
    for k in range(3):
        vals = [r.get(k, 0) / 10 for r in rows]
        bars = ax.bar(x + (k - 1) * width, vals, width, color=colours[k], label=names[k])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f'{v:.1f}%', ha='center',
                    va='bottom', fontsize=10, color=INK)
    ax.set_xticks(x, [f'{n} glasses,\n{m} candidate views' for n, m in sizes], fontsize=11)
    ax.set_ylabel('share of 1000 random scenes', fontsize=11)
    ax.set_ylim(0, 110)
    ax.set_yticks([0, 25, 50, 75, 100], ['0%', '25%', '50%', '75%', '100%'])
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False, fontsize=10, loc='upper right', ncol=3,
              bbox_to_anchor=(1.0, 1.12))
    ax.set_title('How many views greedy uses, compared with the smallest possible',
                 fontsize=12, weight='bold', pad=30)
    _save(fig, SET_COVER, 'random-trials.svg')


# ==========================================================================
# 05_optimisation-solvers
# ==========================================================================

SOLVERS: str = 'optimisation-solvers'

# Four parts on the table and four pockets in a kit tray along the front edge.
PARTS: list[tuple[float, float]] = [(80, 240), (200, 180), (300, 160), (400, 180)]
POCKETS: list[tuple[float, float]] = [(150, 60), (250, 60), (350, 60), (450, 60)]


def assignment_results() -> tuple[tuple[int, ...], float, dict[int, int], float, float]:
    cost = [[math.dist(p, t) for t in POCKETS] for p in PARTS]
    perms = list(itertools.permutations(range(4)))
    totals = {pr: sum(cost[i][pr[i]] for i in range(4)) for pr in perms}
    best = min(perms, key=lambda pr: totals[pr])
    left_p, left_t = set(range(4)), set(range(4))
    greedy: dict[int, int] = {}
    order: list[str] = []
    while left_p:
        i, j = min(((i, j) for i in left_p for j in left_t), key=lambda k: cost[k[0]][k[1]])
        greedy[i] = j
        order.append(f'P{i + 1}->T{j + 1} {cost[i][j]:.1f}')
        left_p.remove(i)
        left_t.remove(j)
    g_total = sum(cost[i][greedy[i]] for i in range(4))
    print('assignment cost matrix (rows parts, columns pockets):')
    for i, row in enumerate(cost):
        print(f'  P{i + 1}: ' + '  '.join(f'{c:6.1f}' for c in row))
    print(f'  best of {len(perms)}: {best} total {totals[best]:.1f} mm; '
          f'worst {max(totals.values()):.1f} mm')
    print(f'  greedy picks in order: {", ".join(order)}; total {g_total:.1f} mm')
    return best, totals[best], greedy, g_total, max(totals.values())


def assignment_greedy_vs_best() -> None:
    best, b_total, greedy, g_total, _ = assignment_results()
    fig, axes = _panels(2, (13, 4.8))
    panels = [('Cheapest pair first', {i: greedy[i] for i in range(4)}, g_total, GRIP),
              ('Best of all 24 assignments', {i: best[i] for i in range(4)}, b_total, SLIDE)]
    for ax, (title, match, total, colour) in zip(axes, panels):
        _axes(ax, (-10, 610), (-40, 420))
        _table(ax)
        ax.add_patch(Rectangle((100, 25), 400, 70, facecolor=LINK_PALE, edgecolor=LINK,
                               lw=1.2, zorder=2))
        _label(ax, 510, 60, 'tray', size=10, color=LINK, ha='left')
        for j, t in enumerate(POCKETS):
            ax.add_patch(Rectangle((t[0] - 26, t[1] - 22), 52, 44, facecolor='white',
                                   edgecolor=LINK, lw=1.4, zorder=3))
            _label(ax, t[0], t[1], f'T{j + 1}', size=10, color=LINK, weight='bold')
        for i, p in enumerate(PARTS):
            _object(ax, p, f'P{i + 1}')
            t = POCKETS[match[i]]
            # A long move would cross the other parts, so it is drawn as a curve
            # that passes above them.
            rad = -0.35 if math.dist(p, t) > 300 else 0.0
            _arrow(ax, p, t, colour, lw=2.2, shrink=22, rad=rad)
            mx, my = (p[0] + t[0]) / 2, (p[1] + t[1]) / 2
            if rad:
                mx, my = mx + 30, my + 85
            _label(ax, mx + 6, my, f'{math.dist(p, t):.0f}', size=9, color=colour,
                   ha='left', weight='bold')
        _title(ax, 300, 440, title)
        _label(ax, 300, -25, f'total travel {total:.0f} mm', size=11, color=colour,
               weight='bold')
        ax.set_ylim(-50, 460)
    _save(fig, SOLVERS, 'assignment-greedy-vs-best.svg')


# The pick order problem: five objects, the arm starts at HOME and ends at BIN.
# C stands in front of B, so C has to be picked before B.
PICKS: dict[str, tuple[float, float]] = {
    'A': (80, 340), 'B': (260, 340), 'C': (280, 240), 'D': (380, 220), 'E': (500, 160),
}
HOME: tuple[float, float] = (40, 0)
BIN: tuple[float, float] = (560, 0)
BEFORE: list[tuple[str, str]] = [('C', 'B')]


def route_length(order: tuple[str, ...]) -> float:
    pts = [HOME] + [PICKS[k] for k in order] + [BIN]
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def allowed(order: tuple[str, ...]) -> bool:
    return all(order.index(a) < order.index(b) for a, b in BEFORE)


def order_results() -> dict[str, tuple[tuple[str, ...], float]]:
    orders = list(itertools.permutations(PICKS))
    ok = [o for o in orders if allowed(o)]
    free = min(orders, key=route_length)
    best = min(ok, key=route_length)
    left, here, greedy = set(PICKS), HOME, []
    while left:
        ready = [k for k in left if all(a not in left for a, b in BEFORE if b == k)]
        k = min(sorted(ready), key=lambda k: math.dist(here, PICKS[k]))
        greedy.append(k)
        left.remove(k)
        here = PICKS[k]
    g = tuple(greedy)
    print(f'pick order: {len(orders)} orders, {len(ok)} keep C before B')
    print(f'  best ignoring the rule {"".join(free)} {route_length(free):.1f} mm')
    print(f'  best keeping the rule  {"".join(best)} {route_length(best):.1f} mm')
    print(f'  nearest-first greedy   {"".join(g)} {route_length(g):.1f} mm')
    print(f'  worst allowed order    {max(route_length(o) for o in ok):.1f} mm')
    return {'free': (free, route_length(free)), 'best': (best, route_length(best)),
            'greedy': (g, route_length(g))}


def pick_order_with_rule() -> None:
    res = order_results()
    fig, axes = _panels(3, (17, 4.9))
    panels = [('Shortest, but breaks the rule', 'free', MUTED),
              ('Shortest that keeps C before B', 'best', SLIDE),
              ('Nearest object first', 'greedy', GRIP)]
    for ax, (title, key, colour) in zip(axes, panels):
        order, length = res[key]
        _axes(ax, (-30, 640), (-70, 530))
        _table(ax)
        pts = [HOME] + [PICKS[k] for k in order] + [BIN]
        for a, b in zip(pts, pts[1:]):
            _arrow(ax, a, b, colour, lw=2.0, shrink=20)
        for k, xy in PICKS.items():
            _object(ax, xy, k, r=20)
        for i, k in enumerate(order):
            x, y = PICKS[k]
            ax.text(x + 17, y + 17, str(i + 1), fontsize=9, ha='center', va='center',
                    color='white', weight='bold', zorder=10,
                    bbox=dict(boxstyle='circle,pad=0.25', facecolor=colour, edgecolor='none'))
        ax.add_patch(Rectangle((HOME[0] - 16, HOME[1] - 16), 32, 32, facecolor=INK, zorder=6))
        _label(ax, HOME[0], HOME[1] - 42, 'start', size=10, color=INK)
        ax.add_patch(Rectangle((BIN[0] - 20, BIN[1] - 16), 40, 32, facecolor=WRIST, zorder=6))
        _label(ax, BIN[0], BIN[1] - 42, 'bin', size=10, color=INK)
        _title(ax, 300, 510, title)
        _label(ax, 300, 470, f'order {" ".join(order)},  {length:.0f} mm', size=11,
               color=colour, weight='bold')
    _save(fig, SOLVERS, 'pick-order-with-rule.svg')


# The packing problem: a box holds at most 6 items and at most 45 kg.
# A small item weighs 5 kg and is worth 5; a large one weighs 9 kg and is worth 8.
SMALL_KG, LARGE_KG, MAX_KG, MAX_ITEMS = 5, 9, 45, 6
SMALL_VAL, LARGE_VAL = 5, 8


def packing_results() -> dict[str, tuple[float, float, float]]:
    # The corners of the region the two limits allow, when fractions are allowed.
    corners = [(0.0, 0.0), (MAX_ITEMS, 0.0), (0.0, MAX_KG / LARGE_KG)]
    y = (MAX_KG - SMALL_KG * MAX_ITEMS) / (LARGE_KG - SMALL_KG)     # both limits met exactly
    corners.append((MAX_ITEMS - y, y))
    value = lambda x, y: SMALL_VAL * x + LARGE_VAL * y             # noqa: E731
    lp = max(corners, key=lambda c: value(*c))
    ints = [(x, y) for x in range(MAX_ITEMS + 1) for y in range(MAX_ITEMS + 1)
            if x + y <= MAX_ITEMS and SMALL_KG * x + LARGE_KG * y <= MAX_KG]
    best = max(ints, key=lambda c: value(*c))
    rounded = (math.floor(lp[0]), math.floor(lp[1]))
    print(f'packing: fractional best {lp} worth {value(*lp):.2f}; rounded down {rounded} '
          f'worth {value(*rounded)}; whole-number best {best} worth {value(*best)}; '
          f'{len(ints)} whole-number choices fit')
    return {'lp': (*lp, value(*lp)), 'rounded': (*rounded, value(*rounded)),
            'best': (*best, value(*best))}


def packing_integer_points() -> None:
    res = packing_results()
    fig, ax = plt.subplots(figsize=(8.2, 6.4), facecolor='white')
    lp_x, lp_y, _ = res['lp']
    region = [(0, 0), (MAX_ITEMS, 0), (lp_x, lp_y), (0, MAX_KG / LARGE_KG)]
    ax.add_patch(Polygon(region, closed=True, facecolor=LINK_PALE, edgecolor='none', zorder=1))
    xs = np.linspace(0, 7, 50)
    ax.plot(xs, MAX_ITEMS - xs, color=LINK, lw=1.8, zorder=2)
    ax.plot(xs, (MAX_KG - SMALL_KG * xs) / LARGE_KG, color=WRIST, lw=1.8, zorder=2)
    ax.text(5.05, 1.25, 'at most 6 items', color=LINK, fontsize=10, rotation=-45,
            ha='center', va='center')
    ax.text(5.0, 2.55, 'at most 45 kg', color=WRIST, fontsize=10, rotation=-29,
            ha='center', va='center')
    for x in range(8):
        for y in range(7):
            fits = x + y <= MAX_ITEMS and SMALL_KG * x + LARGE_KG * y <= MAX_KG
            ax.plot(x, y, 'o', ms=6 if fits else 4, color=INK if fits else GRID, zorder=3)
    white = dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.9)
    for key, colour, marker, text, tx, ty in [
            ('lp', JOINT, '*', 'best with fractions', 2.55, 4.3),
            ('rounded', GRIP, 's', 'fractions rounded down', 4.1, 3.35),
            ('best', SLIDE, 'D', 'best whole numbers', 0.35, 6.25)]:
        x, y, v = res[key]
        ax.plot(x, y, marker, ms=15 if marker == '*' else 11, color=colour, zorder=5,
                markeredgecolor='white')
        label = f'{text}\n{x:g} small, {y:g} large, worth {v:g}'
        ax.annotate(label, (x, y), (tx, ty), fontsize=10, color=colour, weight='bold',
                    zorder=6, va='center', bbox=white,
                    arrowprops=dict(arrowstyle='-', color=colour, lw=1.0,
                                    shrinkA=2, shrinkB=8))
    ax.set_xlim(-0.3, 7.6)
    ax.set_ylim(-0.3, 6.8)
    ax.set_aspect('equal')
    ax.set_xlabel('small items (5 kg, worth 5 each)', fontsize=11)
    ax.set_ylabel('large items (9 kg, worth 8 each)', fontsize=11)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_title('The shaded area obeys both limits; only the dots are whole numbers',
                 fontsize=12, weight='bold')
    _save(fig, SOLVERS, 'packing-integer-points.svg')


# Plain Python checked about 630,000 orders a second on the machine this was
# written on (ten places, 3,628,800 orders in 5.76 s).
ORDERS_PER_SECOND: float = 630_000.0


def orders_grow() -> None:
    ns = list(range(4, 16))
    counts = [math.factorial(n) for n in ns]
    print('orders to try, and plain-Python time at 630,000 a second:')
    for n, c in zip(ns, counts):
        print(f'  {n:2d} places: {c:>16,d} orders, {c / ORDERS_PER_SECOND:12.3f} s')
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor='white')
    secs = [c / ORDERS_PER_SECOND for c in counts]
    colours = [SLIDE if s < 1 else (JOINT if s < 3600 else GRIP) for s in secs]
    ax.bar(ns, secs, color=colours, width=0.7)
    ax.set_yscale('log')
    for s, text in [(1, '1 second'), (60, '1 minute'), (3600, '1 hour'), (86400, '1 day')]:
        ax.axhline(s, color=MUTED, lw=0.8, ls='--', zorder=0)
        ax.text(3.4, s * 1.25, text, fontsize=9, color=MUTED, ha='left', va='bottom')
    ax.set_xticks(ns)
    ax.set_xlabel('number of places to visit', fontsize=11)
    ax.set_ylabel('time to try every order (s)', fontsize=11)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_title('Trying every order: under a second up to nine places, hours from thirteen',
                 fontsize=12, weight='bold')
    _save(fig, SOLVERS, 'orders-grow.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    print('what each view sees:', {v: ''.join(sorted(s)) for v, s in SETS.items()})
    print('greedy:', greedy_cover(set(GLASSES), SETS))
    print('best:', best_cover(set(GLASSES), SETS))
    views_and_footprints()
    greedy_steps()
    greedy_against_best()
    random_trials()
    assignment_greedy_vs_best()
    pick_order_with_rule()
    packing_integer_points()
    orders_grow()


if __name__ == '__main__':
    main()
