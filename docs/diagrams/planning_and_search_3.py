"""Generate the diagrams for visibility, next-best-view and topological sort.

The documents are in docs/06_programming-techniques/06_planning-and-search/03_also-used/:
03_visibility-and-next-best-view.md, and the topological sort section of
01_graph-search.md. Each picture illustrates one idea from its own document,
and goes to docs/images/planning-and-search/<doc-name>/.

Run with:  pixi run python ../docs/diagrams/planning_and_search_3.py
Add --png <folder> to also write PNG copies for checking by eye.

Every picture here shows the result of a real run. The script tests sight
lines against upright cylinders with the exact interval test the page
describes, shades what two cameras cannot see, runs the greedy next-best-view
loop on a grid of unknown cells, and runs Kahn's algorithm on two small
"what must move first" graphs. It prints the numbers the documents quote.
"""

import math
import pathlib
import sys
from collections import deque

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

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
TABLE: str = '#eadfcb'
SHADOW: str = '#4a4a4a'
UNKNOWN: str = '#d9d9d9'
NEW: str = '#f6d98a'

VIS: str = 'visibility-and-next-best-view'
GRAPH: str = 'graph-search'

Point = tuple[float, float]


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
           ha: str = 'center', weight: str = 'normal', box: bool = False) -> None:
    kw = {}
    if box:
        kw['bbox'] = dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.9)
    ax.text(x, y, text, fontsize=size, ha=ha, va='center', color=color, weight=weight,
            zorder=12, **kw)


def _title(ax: Axes, text: str, size: float = 12) -> None:
    ax.set_title(text, fontsize=size, color=INK, weight='bold', pad=8)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# ==========================================================================
# visibility: the scene and the exact sight-line test against a cylinder
# ==========================================================================
#
# Units are centimetres. The table top is z = 0. Four upright cylinders stand
# in a row along the line y = 0: two tall bottles and two short cups. Each is
# (centre x, centre y, radius, height).

CYL: dict[str, tuple[float, float, float, float]] = {
    'bottle 1': (35.0, 0.0, 4.0, 30.0),
    'cup 1': (50.0, 0.0, 4.0, 10.0),
    'bottle 2': (70.0, 0.0, 3.5, 26.0),
    'cup 2': (82.0, 0.0, 5.0, 8.0),
}
TALL = ('bottle 1', 'bottle 2')


def cylinder_intervals(a: tuple[float, float, float], b: tuple[float, float, float],
                       cyl: tuple[float, float, float, float]
                       ) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
    """The two stretches of the segment a->b that are inside the cylinder's two limits.

    A point on the segment is a + t (b - a), with t from 0 at the camera to 1
    at the target. The first stretch is where the point is inside the circle
    seen from above. The second is where it is between the table and the top.
    """
    cx, cy, r, h = cyl
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    fx, fy = a[0] - cx, a[1] - cy
    qa = dx * dx + dy * dy
    qb = 2 * (fx * dx + fy * dy)
    qc = fx * fx + fy * fy - r * r
    if qa < 1e-12:                       # a straight-down ray: inside or not, all along
        top = (-math.inf, math.inf) if qc <= 0 else None
    else:
        disc = qb * qb - 4 * qa * qc
        if disc < 0:
            top = None
        else:
            s = math.sqrt(disc)
            top = ((-qb - s) / (2 * qa), (-qb + s) / (2 * qa))
    if abs(dz) < 1e-12:                  # a level ray: at one height all along
        side = (-math.inf, math.inf) if 0 <= a[2] <= h else None
    else:
        t0, t1 = (0 - a[2]) / dz, (h - a[2]) / dz
        side = (min(t0, t1), max(t0, t1))
    return top, side


def blocked_by(a: tuple[float, float, float], b: tuple[float, float, float],
               cyl: tuple[float, float, float, float], eps: float = 1e-6) -> bool:
    """True if the solid cylinder cuts the segment somewhere strictly before the target."""
    top, side = cylinder_intervals(a, b, cyl)
    if top is None or side is None:
        return False
    lo = max(top[0], side[0], 0.0)
    hi = min(top[1], side[1], 1.0 - eps)
    return lo < hi


def visible(cam: Point, p: Point) -> bool:
    """Sight line inside the slice y = 0, from a camera to a point, both as (x, z)."""
    a = (cam[0], 0.0, cam[1])
    b = (p[0], 0.0, p[1])
    return not any(blocked_by(a, b, c) for c in CYL.values())


def inside_object(x: float, z: float) -> bool:
    return any(abs(x - cx) <= r and 0 <= z <= h for cx, _cy, r, h in CYL.values())


def _draw_slice(ax: Axes, labels: bool = True, size: float = 9.5) -> None:
    """The row of cylinders seen from the side: each one is a rectangle."""
    ax.add_patch(Rectangle((-4, -3), 108, 3, facecolor=TABLE, edgecolor='none', zorder=2))
    for name, (cx, _cy, r, h) in CYL.items():
        col = LINK if name in TALL else WRIST
        ax.add_patch(Rectangle((cx - r, 0), 2 * r, h, facecolor=col, edgecolor='white',
                               lw=1, zorder=6))
        if labels:
            _label(ax, cx, h + 2.2, name, size=size, box=True)


def _camera(ax: Axes, p: Point, aim: Point, colour: str = INK, size: float = 2.6,
            text: str | None = None, text_offset: Point = (0.0, 4.0),
            tsize: float = 10) -> None:
    """A small camera: a dot with a short wedge pointing where it looks."""
    ang = math.atan2(aim[1] - p[1], aim[0] - p[0])
    w = math.radians(28)
    tip1 = (p[0] + size * 1.6 * math.cos(ang - w), p[1] + size * 1.6 * math.sin(ang - w))
    tip2 = (p[0] + size * 1.6 * math.cos(ang + w), p[1] + size * 1.6 * math.sin(ang + w))
    ax.add_patch(Polygon([p, tip1, tip2], closed=True, facecolor=colour, edgecolor='white',
                         lw=0.8, zorder=10))
    ax.add_patch(Circle(p, size * 0.55, facecolor=colour, edgecolor='white', lw=0.8,
                        zorder=11))
    if text:
        _label(ax, p[0] + text_offset[0], p[1] + text_offset[1], text, size=tsize,
               color=colour, weight='bold', box=True)


# --------------------------------------------------------------------------
# picture 1: what a side camera and a top camera cannot see
# --------------------------------------------------------------------------

SIDE_CAM: Point = (0.0, 20.0)
TOP_CAM: Point = (50.0, 60.0)


def shadow_fraction(cam: Point, step: float = 0.25) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Test a fine grid of points in the free space of the slice."""
    xs = np.arange(0, 100 + 1e-9, step)
    zs = np.arange(0, 45 + 1e-9, step)
    hidden = np.zeros((len(zs), len(xs)), dtype=bool)
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            if not inside_object(x, z) and not visible(cam, (x, z)):
                hidden[j, i] = True
    return xs, zs, hidden


def seen_from_side_and_above() -> None:
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.2), facecolor='white')
    for ax, cam, name in ((axs[0], SIDE_CAM, 'side'), (axs[1], TOP_CAM, 'top')):
        _axes(ax, (-6, 106), (-12, 66))
        xs, zs, hidden = shadow_fraction(cam)
        img = np.where(hidden, 1.0, np.nan)
        ax.imshow(img, extent=(xs[0], xs[-1], zs[0], zs[-1]), origin='lower',
                  cmap=matplotlib.colors.ListedColormap([SHADOW]), alpha=0.28,
                  interpolation='nearest', zorder=3, aspect='auto')
        _draw_slice(ax)
        # the sight lines that graze a corner: past the corner they carry on,
        # and everything beyond them on the far side is in the object's shadow
        for _nm, (cx, _cy, r, h) in CYL.items():
            for corner in ((cx - r, h), (cx + r, h)):
                d = np.array(corner) - np.array(cam)
                d = d / np.linalg.norm(d)
                just_past = np.array(corner) + d * 0.3
                if not visible(cam, corner) or inside_object(*just_past):
                    continue
                end = just_past
                while 0 <= end[0] <= 100 and 0 <= end[1] <= 45 and not inside_object(*end):
                    end = end + d * 0.2
                ax.plot([cam[0], end[0]], [cam[1], end[1]], '-', color=MUTED, lw=0.8,
                        zorder=4)
        ax.add_patch(Rectangle((0, 0), 100, 45, facecolor='none', edgecolor=MUTED,
                               lw=0.8, ls='--', zorder=2))
        _camera(ax, cam, (50, 5), colour=GRIP, text=f'{name} camera',
                text_offset=(8, -6) if name == 'side' else (0, 5))
        vis_objs = []
        for nm, (cx, _cy, r, h) in CYL.items():
            top_pts = [(cx + r * u, h + 0.01) for u in np.linspace(-0.9, 0.9, 7)]
            frac = sum(visible(cam, p) for p in top_pts) / len(top_pts)
            vis_objs.append((nm, frac))
        seen = ', '.join(nm + ('' if f == 1 else ' (partly)') for nm, f in vis_objs
                         if f > 0) or 'none'
        hid = ', '.join(nm for nm, f in vis_objs if f == 0) or 'none'
        _label(ax, 50, -8.5, f'tops in view: {seen}\ntops hidden: {hid}', size=9.5,
               color=INK)
        pct = 100 * hidden.sum() / (~np.vectorize(inside_object)(*np.meshgrid(xs, zs))).sum()
        _title(ax, f'From the {name}: {pct:.0f}% of the free space is hidden')
        print(f'{name} camera at {cam}: {pct:.1f}% of free space (up to 45 cm) hidden; '
              f'top faces seen: {vis_objs}')
    fig.tight_layout()
    _save(fig, VIS, 'seen-from-side-and-above.svg')


# --------------------------------------------------------------------------
# picture 2: the exact sight-line test against a cylinder
# --------------------------------------------------------------------------

TEST_CAM: tuple[float, float, float] = (0.0, -10.0, 30.0)
RAYS: list[tuple[str, tuple[float, float, float], str]] = [
    ('ray 1: to the top of cup 1', (50.0, 0.0, 10.0), GRIP),
    ('ray 2: to the top of bottle 2', (70.0, 0.0, 26.0), SLIDE),
]


def cylinder_sight_line_test() -> None:
    fig = plt.figure(figsize=(13, 7.6), facecolor='white')
    ax_top = fig.add_axes((0.02, 0.50, 0.46, 0.46))
    ax_side = fig.add_axes((0.52, 0.50, 0.46, 0.46))
    ax_t = fig.add_axes((0.30, 0.07, 0.66, 0.38))

    # from above
    _axes(ax_top, (-6, 92), (-18, 22))
    ax_top.add_patch(Rectangle((-4, -16), 94, 26, facecolor=TABLE, edgecolor='none', zorder=1))
    for name, (cx, cy, r, _h) in CYL.items():
        col = LINK if name in TALL else WRIST
        ax_top.add_patch(Circle((cx, cy), r, facecolor=col, edgecolor='white', lw=1, zorder=4))
        _label(ax_top, cx, cy + r + 2.4, name, size=9, box=True)
    for _txt, tgt, col in RAYS:
        ax_top.plot([TEST_CAM[0], tgt[0]], [TEST_CAM[1], tgt[1]], '-', color=col, lw=2.2,
                    zorder=6)
    _camera(ax_top, (TEST_CAM[0], TEST_CAM[1]), (50, 0), colour=INK, size=2.2,
            text='camera', text_offset=(2, -4.5), tsize=9)
    _title(ax_top, 'From above: each cylinder is a circle', 11.5)
    _label(ax_top, 50, -13, 'red crosses bottle 1.  Green crosses cup 1 and misses bottle 1.',
           size=9.5)

    # from the side
    _axes(ax_side, (-6, 92), (-9, 36))
    ax_side.add_patch(Rectangle((-4, -3), 94, 3, facecolor=TABLE, edgecolor='none', zorder=1))
    for name, (cx, _cy, r, h) in CYL.items():
        col = LINK if name in TALL else WRIST
        ax_side.add_patch(Rectangle((cx - r, 0), 2 * r, h, facecolor=col, edgecolor='white',
                                    lw=1, zorder=4))
    for _txt, tgt, col in RAYS:
        ax_side.plot([TEST_CAM[0], tgt[0]], [TEST_CAM[2], tgt[2]], '-', color=col, lw=2.2,
                     zorder=6)
    _camera(ax_side, (TEST_CAM[0], TEST_CAM[2]), (50, 10), colour=INK, size=2.0)
    _title(ax_side, 'From the side: each cylinder is a rectangle', 11.5)
    _label(ax_side, 45, -6.5, 'red is below the top of bottle 1.  Green is above cup 1 '
           'and level with the top of bottle 1.', size=9.5)

    # along each ray
    ax_t.set_facecolor('white')
    ax_t.set_xlim(0, 1.0)
    ax_t.set_ylim(-0.4, 6.4)
    for s in ('top', 'right', 'left'):
        ax_t.spines[s].set_visible(False)
    ax_t.set_yticks([])
    ax_t.tick_params(colors=INK, labelsize=9.5)
    ax_t.set_xlabel('t, the fraction of the way from the camera (0) to the target (1)',
                    fontsize=10.5, color=INK)
    tests = [(0, 'bottle 1', 5.2), (1, 'cup 1', 3.0), (1, 'bottle 1', 0.8)]
    for ray_i, cname, y0 in tests:
        txt, tgt, col = RAYS[ray_i]
        top, side = cylinder_intervals(TEST_CAM, tgt, CYL[cname])
        hit = blocked_by(TEST_CAM, tgt, CYL[cname])
        colour_name = 'red' if ray_i == 0 else 'green'
        ax_t.text(-0.03, y0 + 0.95, f'{colour_name} ray against {cname}', fontsize=10.5,
                  ha='right', va='center', color=col, weight='bold')
        for k, (iv, what) in enumerate(((top, 'inside the circle'),
                                        (side, 'below the top'))):
            yy = y0 + 0.35 - k * 0.6
            if iv is None:
                desc = 'never'
            else:
                desc = f't = {iv[0] + 0.0:.2f} to {iv[1] + 0.0:.2f}'
            ax_t.text(-0.03, yy, f'{what}: {desc}', fontsize=9.5, ha='right', va='center',
                      color=INK)
            if iv is not None:
                lo, hi = max(iv[0], 0.0), min(iv[1], 1.0)
                if lo < hi:
                    ax_t.add_patch(Rectangle((lo, yy - 0.2), hi - lo, 0.4, facecolor=col,
                                             alpha=0.35, edgecolor=col))
                else:
                    ax_t.text(0.5, yy, 'only past the target, so not on this line',
                              fontsize=9, ha='center', va='center', color=MUTED)
        if hit:
            lo, hi = max(top[0], side[0], 0.0), min(top[1], side[1], 1.0)
            ax_t.add_patch(Rectangle((lo, y0 - 0.5), hi - lo, 1.2, facecolor='none',
                                     edgecolor=GRIP, lw=2))
            verdict = f'both at once for t = {lo:.2f} to {hi:.2f}: blocked'
        else:
            verdict = 'never both at once: not blocked'
        ax_t.text(1.0, y0 + 0.95, verdict, fontsize=10, ha='right', va='center',
                  color=GRIP if hit else SLIDE, weight='bold')
        print(f'{txt} vs {cname}: circle {top}, height {side}, blocked {hit}')
    _save(fig, VIS, 'cylinder-sight-line-test.svg')
    for txt, tgt, _col in RAYS:
        for name, c in CYL.items():
            print(f'  {txt} vs {name}: blocked {blocked_by(TEST_CAM, tgt, c)}')


# --------------------------------------------------------------------------
# pictures 3 and 4: candidate views, reach, and the greedy next-best-view loop
# --------------------------------------------------------------------------

CELL: float = 2.0            # unknown-space cells are 2 cm squares in the slice
TOP_Z: float = 32.0          # the space of interest runs up to 32 cm above the table
FOV: float = 70.0            # the camera's field of view in degrees, across the slice
AIM: Point = (50.0, 5.0)     # every candidate looks at this point
ARC: float = 55.0            # candidates sit on an arc of this radius round the table centre
ANGLES: list[int] = list(range(15, 166, 15))
BASE: Point = (-10.0, 0.0)   # the arm's shoulder
REACH: float = 100.0         # the furthest the arm can hold the camera from its shoulder
BUDGET: int = 3


def unknown_cells() -> list[Point]:
    xs = np.arange(0, 100, CELL) + CELL / 2
    zs = np.arange(0, TOP_Z, CELL) + CELL / 2
    return [(float(x), float(z)) for x in xs for z in zs if not inside_object(x, z)]


def candidates() -> list[dict]:
    out = []
    for th in ANGLES:
        p = (50 + ARC * math.cos(math.radians(th)), ARC * math.sin(math.radians(th)))
        dist = math.hypot(p[0] - BASE[0], p[1] - BASE[1])
        out.append({'angle': th, 'pos': p, 'reach': dist, 'ok': dist <= REACH})
    return out


def cells_seen(cam: Point, cells: list[Point]) -> set[int]:
    ang0 = math.atan2(AIM[1] - cam[1], AIM[0] - cam[0])
    out = set()
    for i, (x, z) in enumerate(cells):
        a = math.atan2(z - cam[1], x - cam[0])
        da = (a - ang0 + math.pi) % (2 * math.pi) - math.pi
        if abs(da) <= math.radians(FOV / 2) and visible(cam, (x, z)):
            out.add(i)
    return out


def objects_seen(cam: Point) -> list[str]:
    """An object counts as seen when some of its top face is in view and not hidden."""
    ang0 = math.atan2(AIM[1] - cam[1], AIM[0] - cam[0])
    names = []
    for nm, (cx, _cy, r, h) in CYL.items():
        pts = [(cx + r * u, h + 0.01) for u in np.linspace(-0.9, 0.9, 7)]
        ok = 0
        for p in pts:
            a = math.atan2(p[1] - cam[1], p[0] - cam[0])
            da = (a - ang0 + math.pi) % (2 * math.pi) - math.pi
            if abs(da) <= math.radians(FOV / 2) and visible(cam, p):
                ok += 1
        if ok:
            names.append(nm)
    return names


def next_best_view() -> dict:
    cells = unknown_cells()
    cands = candidates()
    for c in cands:
        c['sees'] = cells_seen(c['pos'], cells)
        c['objects'] = objects_seen(c['pos'])
    known: set[int] = set()
    chosen: list[int] = []
    rounds = []
    for _ in range(BUDGET):
        gains = {c['angle']: len(c['sees'] - known) for c in cands
                 if c['ok'] and c['angle'] not in chosen}
        best = max(gains, key=lambda k: (gains[k], -k))
        new = next(c for c in cands if c['angle'] == best)['sees'] - known
        rounds.append({'gains': gains, 'best': best, 'new': new, 'before': set(known)})
        chosen.append(best)
        known |= new
    return {'cells': cells, 'cands': cands, 'rounds': rounds, 'known': known}


def _draw_cells(ax: Axes, cells: list[Point], shade: dict[int, str]) -> None:
    for i, (x, z) in enumerate(cells):
        ax.add_patch(Rectangle((x - CELL / 2, z - CELL / 2), CELL, CELL,
                               facecolor=shade.get(i, UNKNOWN), edgecolor='white', lw=0.4,
                               zorder=2))


def candidate_views(run: dict) -> None:
    cells, cands, r1 = run['cells'], run['cands'], run['rounds'][0]
    fig, ax = plt.subplots(figsize=(12, 7.4), facecolor='white')
    _axes(ax, (-16, 116), (-13, 66))
    _draw_cells(ax, cells, {})
    _draw_slice(ax, labels=True, size=9)
    # the arm's reach
    th = np.linspace(0, math.pi / 2, 200)
    ax.plot(BASE[0] + REACH * np.cos(th), BASE[1] + REACH * np.sin(th), '--', color=MUTED,
            lw=1.2, zorder=3)
    _label(ax, 91, -5.5, 'edge of the arm\'s reach', size=9, color=MUTED)
    ax.add_patch(Circle(BASE, 2.2, facecolor=INK, zorder=8))
    _label(ax, BASE[0], BASE[1] - 4.5, 'shoulder', size=9)
    best = r1['best']
    for c in cands:
        p = c['pos']
        col = GRIP if c['angle'] == best else (LINK if c['ok'] else OBSTACLE)
        _camera(ax, p, AIM, colour=col, size=2.2)
        dx, dy = p[0] - 50, p[1]
        n = math.hypot(dx, dy)
        lx, ly = p[0] + dx / n * 8, p[1] + dy / n * 8
        if c['ok']:
            txt = f"{c['angle']}°\n{len(c['sees'])} new"
        else:
            txt = f"{c['angle']}°\nout of reach"
        _label(ax, lx, ly, txt, size=8.5, color=col, weight='bold' if c['angle'] == best else
               'normal')
        if c['angle'] == best:
            ang0 = math.atan2(AIM[1] - p[1], AIM[0] - p[0])
            for s in (-1, 1):
                a = ang0 + s * math.radians(FOV / 2)
                end = np.array(p, dtype=float)
                while end[1] > 0 and not inside_object(*end):
                    end = end + 0.2 * np.array([math.cos(a), math.sin(a)])
                ax.plot([p[0], end[0]], [p[1], end[1]], ':', color=GRIP, lw=1.3, zorder=3)
    _label(ax, 45, -11, f'grey squares: {len(cells)} cells of unknown space, 2 cm each.  '
           'Each camera is labelled with its angle round the table and the cells it would see.',
           size=9.5)
    _title(ax, f'Round 1: 11 candidate views, 3 out of reach; the best sees {len(r1["new"])} '
           'cells')
    _save(fig, VIS, 'candidate-views-and-reach.svg')


def three_rounds(run: dict) -> None:
    cells, cands, rounds = run['cells'], run['cands'], run['rounds']
    fig, axs = plt.subplots(1, BUDGET, figsize=(15.5, 4.6), facecolor='white')
    for k, (ax, rd) in enumerate(zip(axs, rounds)):
        _axes(ax, (-6, 106), (-12, 62))
        shade = {i: LINK_PALE for i in rd['before']}
        shade.update({i: NEW for i in rd['new']})
        _draw_cells(ax, cells, shade)
        _draw_slice(ax, labels=False)
        for j, prev in enumerate(rounds[:k]):
            c = next(c for c in cands if c['angle'] == prev['best'])
            _camera(ax, c['pos'], AIM, colour=LINK, size=2.0)
        c = next(c for c in cands if c['angle'] == rd['best'])
        _camera(ax, c['pos'], AIM, colour=GRIP, size=2.4)
        known_after = len(rd['before']) + len(rd['new'])
        _title(ax, f"Round {k + 1}: take {rd['best']}°, +{len(rd['new'])} cells", 11.5)
        _label(ax, 50, -7, f'known {known_after} of {len(cells)} '
               f'({100 * known_after / len(cells):.0f}%)', size=10)
    fig.text(0.5, 0.06, 'yellow: newly seen this round   pale blue: seen in earlier rounds   '
             'grey: still unknown   red camera: this round\'s choice', ha='center',
             fontsize=10, color=INK)
    fig.tight_layout()
    _save(fig, VIS, 'three-rounds-of-next-best-view.svg')


def nbv_numbers(run: dict) -> None:
    print(f"unknown cells: {len(run['cells'])}")
    for c in run['cands']:
        print(f"  candidate {c['angle']:3d} deg at ({c['pos'][0]:.1f}, {c['pos'][1]:.1f}), "
              f"{c['reach']:.1f} cm from the shoulder, reachable {c['ok']}, sees "
              f"{len(c['sees'])} cells, objects {c['objects']}")
    for k, rd in enumerate(run['rounds']):
        known = len(rd['before']) + len(rd['new'])
        print(f"  round {k + 1}: gains {rd['gains']} -> take {rd['best']}, "
              f"+{len(rd['new'])}, known {known} ({100 * known / len(run['cells']):.1f}%)")


# ==========================================================================
# topological sort: which object must move first
# ==========================================================================
#
# An arrow u -> v means "u must be moved before v". It comes from one of two
# facts: u rests on v, or u stands in the way of the gripper reaching v.

TOPO_NODES: list[str] = ['tray', 'box', 'book', 'cup', 'bottle']
TOPO_EDGES: list[tuple[str, str, str]] = [
    ('book', 'box', 'rests on'),
    ('box', 'tray', 'rests on'),
    ('cup', 'tray', 'rests on'),
    ('bottle', 'cup', 'in the way'),
]
TOPO_POS: dict[str, Point] = {'bottle': (0.0, 1.0), 'book': (0.0, 3.0), 'cup': (2.2, 1.0),
                              'box': (2.2, 3.0), 'tray': (4.4, 2.0)}

LOOP_NODES: list[str] = ['block', 'plate A', 'plate B', 'mug']
LOOP_EDGES: list[tuple[str, str, str]] = [
    ('block', 'plate A', 'rests on'),
    ('block', 'plate B', 'rests on'),
    ('plate A', 'plate B', 'leans on'),
    ('plate B', 'plate A', 'leans on'),
    ('plate A', 'mug', 'in the way'),
    ('plate B', 'mug', 'in the way'),
]
LOOP_POS: dict[str, Point] = {'block': (0.0, 2.0), 'plate A': (2.2, 3.0),
                              'plate B': (2.2, 1.0), 'mug': (4.4, 2.0)}


def kahn(nodes: list[str], edges: list[tuple[str, str, str]]) -> dict:
    """Kahn's algorithm. Returns every step, the order, and what is left if it gets stuck."""
    indeg = {n: 0 for n in nodes}
    out: dict[str, list[str]] = {n: [] for n in nodes}
    for u, v, _why in edges:
        out[u].append(v)
        indeg[v] += 1
    ready = deque(n for n in nodes if indeg[n] == 0)
    steps = [{'take': None, 'indeg': dict(indeg), 'ready': list(ready), 'done': []}]
    order: list[str] = []
    while ready:
        n = ready.popleft()
        order.append(n)
        for v in out[n]:
            indeg[v] -= 1
            if indeg[v] == 0:
                ready.append(v)
        steps.append({'take': n, 'indeg': dict(indeg), 'ready': list(ready),
                      'done': list(order)})
    left = [n for n in nodes if n not in order]
    return {'order': order, 'steps': steps, 'left': left}


def find_loop(left: list[str], edges: list[tuple[str, str, str]]) -> list[str]:
    """Start at any stuck object and keep stepping to one of its stuck blockers."""
    blockers = {n: [u for u, v, _w in edges if v == n and u in left] for n in left}
    walk = [left[-1]]
    while walk[-1] not in walk[:-1]:
        walk.append(blockers[walk[-1]][0])
    first = walk.index(walk[-1])
    return walk[first:]


def _graph(ax: Axes, nodes: list[str], edges: list[tuple[str, str, str]],
           pos: dict[str, Point], fill: dict[str, str] | None = None,
           badge: dict[str, str] | None = None, faded: set[str] | None = None,
           hot: set[tuple[str, str]] | None = None, edge_labels: bool = True,
           r: float = 0.46, size: float = 10) -> None:
    faded = faded or set()
    hot = hot or set()
    pairs = {(u, v) for u, v, _w in edges}
    for u, v, why in edges:
        pu, pv = np.array(pos[u]), np.array(pos[v])
        both = (v, u) in pairs
        rad = 0.25 if both else 0.0
        gone = u in faded or v in faded
        col = GRIP if (u, v) in hot else (GRID if gone else INK)
        arr = FancyArrowPatch(tuple(pu), tuple(pv), arrowstyle='-|>', mutation_scale=16,
                              color=col, lw=2.2 if (u, v) in hot else 1.6,
                              shrinkA=r * 72 / 1.0 * 0 + 0, shrinkB=0,
                              connectionstyle=f'arc3,rad={rad}', zorder=3)
        # shorten by hand so the arrow stops at the node's edge
        d = pv - pu
        n = np.linalg.norm(d)
        a = pu + d / n * r
        b = pv - d / n * (r + 0.02)
        arr.set_positions(tuple(a), tuple(b))
        ax.add_patch(arr)
        if edge_labels and not gone:
            m = (a + b) / 2
            normal = np.array([-d[1], d[0]]) / n
            m = m + normal * (rad * n * 0.5 + (0.42 if rad else 0.0))
            _label(ax, m[0], m[1], why, size=8.5, color=MUTED, box=True)
    for nm in nodes:
        x, y = pos[nm]
        gone = nm in faded
        fc = (fill or {}).get(nm, 'white')
        ax.add_patch(Circle((x, y), r, facecolor='#f4f4f4' if gone else fc,
                            edgecolor=GRID if gone else INK, lw=1.5, zorder=5))
        _label(ax, x, y, nm, size=size, color=MUTED if gone else INK)
        if badge and nm in badge:
            ax.add_patch(Circle((x + r * 0.78, y + r * 0.78), 0.2, facecolor=JOINT,
                                edgecolor='white', lw=1, zorder=7))
            _label(ax, x + r * 0.78, y + r * 0.78, badge[nm], size=9, weight='bold')


def what_must_move_first() -> None:
    fig, (ax_s, ax_g) = plt.subplots(1, 2, figsize=(13.5, 5.0), facecolor='white',
                                     gridspec_kw={'width_ratios': [1.05, 1]})
    # the scene from the side; the arm reaches in from the left
    _axes(ax_s, (-6, 92), (-6, 40))
    ax_s.add_patch(Rectangle((-4, -3), 94, 3, facecolor=TABLE, edgecolor='none'))
    parts = [('tray', 40, 0, 44, 2.5, OBSTACLE), ('box', 60, 2.5, 16, 13, LINK),
             ('book', 56, 15.5, 24, 3, PURPLE), ('cup', 45, 2.5, 8, 11, WRIST),
             ('bottle', 24, 0, 7, 29, SLIDE)]
    for nm, x, y, w, h, col in parts:
        ax_s.add_patch(Rectangle((x, y), w, h, facecolor=col, edgecolor='white', lw=1,
                                 zorder=4))
    _label(ax_s, 62, -1.6 + 3.2, '', size=9)
    for nm, x, y, w, h, _c in parts:
        ly = {'tray': 4.0, 'box': 9, 'book': 21, 'cup': 16.5, 'bottle': 31.5}[nm]
        lx = {'tray': 82.5, 'box': 68, 'book': 68, 'cup': 49, 'bottle': 27.5}[nm]
        _label(ax_s, lx, ly, nm, size=10, box=nm not in ('box',),
               color='white' if nm == 'box' else INK)
    ax_s.annotate('', xy=(22, 10), xytext=(2, 10),
                  arrowprops={'arrowstyle': '-|>', 'color': INK, 'lw': 2})
    _label(ax_s, 11, 13, 'gripper\ncomes in', size=9)
    _title(ax_s, 'The table from the side')
    # the graph
    _axes(ax_g, (-0.8, 5.2), (0.2, 3.8))
    _graph(ax_g, TOPO_NODES, TOPO_EDGES, TOPO_POS)
    _title(ax_g, 'An arrow means "move this one before that one"')
    fig.tight_layout()
    _save(fig, GRAPH, 'what-must-move-first.svg')


def kahn_step_by_step(run: dict) -> None:
    steps = run['steps']
    fig, axs = plt.subplots(2, 3, figsize=(14, 7.6), facecolor='white')
    for k, (ax, st) in enumerate(zip(axs.flat, steps)):
        _axes(ax, (-0.8, 5.2), (0.1, 4.1))
        done = set(st['done'])
        badge = {n: str(st['indeg'][n]) for n in TOPO_NODES if n not in done}
        fill = {n: '#e3f3e6' for n in st['ready']}
        _graph(ax, TOPO_NODES, TOPO_EDGES, TOPO_POS, fill=fill, badge=badge, faded=done,
               edge_labels=False, size=9.5)
        if st['take'] is None:
            head = 'Start: count arrows coming in'
        else:
            head = f"Step {k}: take the {st['take']}"
        _title(ax, head, 11.5)
        order = ', '.join(st['done']) if st['done'] else '(empty)'
        ready = ', '.join(st['ready']) if st['ready'] else '(empty)'
        _label(ax, 2.2, 0.3, f'order so far: {order}\nready: {ready}', size=9.5)
    fig.text(0.5, -0.01, 'yellow badge: arrows still coming in   green: ready, nothing '
             'left in its way   grey: already moved', ha='center', fontsize=10, color=INK)
    fig.tight_layout()
    _save(fig, GRAPH, 'kahn-step-by-step.svg')


def a_loop_means_no_order(run: dict, loop: list[str]) -> None:
    fig, (ax_s, ax_g) = plt.subplots(1, 2, figsize=(13.5, 5.0), facecolor='white',
                                     gridspec_kw={'width_ratios': [1.0, 1.05]})
    _axes(ax_s, (-4, 80), (-6, 38))
    ax_s.add_patch(Rectangle((-2, -3), 80, 3, facecolor=TABLE, edgecolor='none'))
    # two plates leaning on each other, a block resting on top, a mug behind
    a = Polygon([(18, 0), (21, 0), (35, 24), (32, 24)], closed=True, facecolor=LINK,
                edgecolor='white', zorder=4)
    b = Polygon([(46, 0), (49, 0), (35, 24), (32, 24)], closed=True, facecolor=PURPLE,
                edgecolor='white', zorder=4)
    ax_s.add_patch(a)
    ax_s.add_patch(b)
    ax_s.add_patch(Rectangle((29, 24), 9, 6, facecolor=JOINT, edgecolor='white', zorder=5))
    ax_s.add_patch(Rectangle((29.5, 0), 8, 9, facecolor=WRIST, edgecolor='white', zorder=4))
    _label(ax_s, 22, 13, 'plate A', size=10, ha='right', box=True)
    _label(ax_s, 45, 13, 'plate B', size=10, ha='left', box=True)
    _label(ax_s, 33.5, 33, 'block', size=10, box=True)
    _label(ax_s, 33.5, 4.5, 'mug', size=9.5, color='white')
    _title(ax_s, 'Two plates leaning on each other, a mug under them')
    _axes(ax_g, (-0.8, 5.2), (0.2, 3.9))
    loop_edges = {(loop[i + 1], loop[i]) for i in range(len(loop) - 1)}
    done = set(run['order'])
    badge = {n: str(run['steps'][-1]['indeg'][n]) for n in LOOP_NODES if n not in done}
    _graph(ax_g, LOOP_NODES, LOOP_EDGES, LOOP_POS, badge=badge, faded=done, hot=loop_edges,
           fill={n: '#fbe0e0' for n in run['left']})
    _title(ax_g, f"Kahn moves the {', '.join(run['order'])}, then nothing is ready")
    _label(ax_g, 2.2, 0.35, 'red arrows: the loop.  The mug is stuck too, but only because '
           'it waits on the plates.', size=9.5)
    fig.tight_layout()
    _save(fig, GRAPH, 'a-loop-means-no-order.svg')


def topo_numbers(run: dict, loop_run: dict, loop: list[str]) -> None:
    for st in run['steps']:
        print(f"  take {st['take']}: in-degrees {st['indeg']}, ready {st['ready']}")
    print(f"  order: {run['order']}")
    print(f"  loop scene: order {loop_run['order']}, stuck {loop_run['left']}, loop {loop}")
    for st in loop_run['steps']:
        print(f"    take {st['take']}: in-degrees {st['indeg']}, ready {st['ready']}")


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    seen_from_side_and_above()
    cylinder_sight_line_test()
    run = next_best_view()
    candidate_views(run)
    three_rounds(run)
    nbv_numbers(run)
    topo = kahn(TOPO_NODES, TOPO_EDGES)
    what_must_move_first()
    kahn_step_by_step(topo)
    loop_run = kahn(LOOP_NODES, LOOP_EDGES)
    loop = find_loop(loop_run['left'], LOOP_EDGES)
    a_loop_means_no_order(loop_run, loop)
    topo_numbers(topo, loop_run, loop)
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
