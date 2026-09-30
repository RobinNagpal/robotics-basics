"""Generate the diagrams for the first half of docs/05_programming-techniques/06_planning-and-search/.

This covers 01_overview, 02_graph-search and 03_sampling-based-planning. Each
document's pictures go to a folder named after it, under
docs/images/planning-and-search/.

Run with:  pixi run python ../docs/diagrams/planning_and_search_1.py
Add --png <dir> to also write PNG copies for checking.

Every picture that shows an algorithm's result is the real result. The script
runs breadth-first search, Dijkstra's algorithm and A* on the drawn grid, and
runs RRT, RRT-Connect and PRM on the configuration space of the book's two-joint
arm (link 1 is 3 m, link 2 is 2 m). The random planners use fixed seeds, so the
pictures are the same every time the script runs. The numbers the documents
quote come from the same functions; run with --numbers to print them.
"""

import heapq
import pathlib
import sys
from collections import deque

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'planning-and-search'
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

OBST: str = '#5b5b5b'           # an occupied grid cell
EXPANDED: str = '#fbe3b0'       # a cell the search took off its list and looked at
COSTLY: str = '#f6cccc'         # a cell that costs more to enter


# --------------------------------------------------------------------------
# small drawing helpers
# --------------------------------------------------------------------------

def _axes(ax: Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')


def _title(ax: Axes, text: str, size: float = 12) -> None:
    ax.set_title(text, fontsize=size, color=INK, weight='bold', pad=10)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# ==========================================================================
# PART 1: graph search on a grid and on a small roadmap
# ==========================================================================

# The table seen from above, cut into 5 cm squares: 16 across and 10 deep.
# The gripper moves at a fixed height. A square is occupied when something on
# the table stands taller than that height.
GW: int = 16
GH: int = 10
START: tuple[int, int] = (1, 5)
GOAL: tuple[int, int] = (14, 4)


def grid_map() -> np.ndarray:
    """True where a square is occupied. Indexed [x, y], y = 0 at the bottom."""
    occ: np.ndarray = np.zeros((GW, GH), bool)
    occ[5:8, 2:9] = True        # a box
    occ[10:12, 0:3] = True      # a tray of parts
    occ[10:12, 6:10] = True     # a bottle and a jar
    return occ


def _neighbours(c: tuple[int, int], occ: np.ndarray) -> list[tuple[int, int]]:
    x, y = c
    out: list[tuple[int, int]] = []
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < GW and 0 <= ny < GH and not occ[nx, ny]:
            out.append((nx, ny))
    return out


def _path_back(parent: dict, goal: tuple[int, int]) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = [goal]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    return path[::-1]


def bfs(occ: np.ndarray) -> tuple[dict, list, list]:
    """Breadth-first search. Returns step counts, the path, and the cells taken off the list."""
    steps: dict = {START: 0}
    parent: dict = {START: None}
    queue: deque = deque([START])
    taken: list = []
    while queue:
        c = queue.popleft()
        taken.append(c)
        if c == GOAL:
            break
        for n in _neighbours(c, occ):
            if n not in steps:
                steps[n] = steps[c] + 1
                parent[n] = c
                queue.append(n)
    return steps, _path_back(parent, GOAL), taken


def enter_cost(occ: np.ndarray, clearance_cost: float) -> np.ndarray:
    """Cost to move into each square: 1, or clearance_cost next to something occupied."""
    cost: np.ndarray = np.ones((GW, GH))
    for x in range(GW):
        for y in range(GH):
            if occ[x, y]:
                continue
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GW and 0 <= ny < GH and occ[nx, ny]:
                        cost[x, y] = clearance_cost
    return cost


def best_first(occ: np.ndarray, cost: np.ndarray, use_heuristic: bool) -> tuple[dict, list, list]:
    """Dijkstra's algorithm (use_heuristic False) or A* (True, Manhattan distance)."""
    def h(c: tuple[int, int]) -> float:
        return abs(c[0] - GOAL[0]) + abs(c[1] - GOAL[1]) if use_heuristic else 0.0

    g: dict = {START: 0.0}
    parent: dict = {START: None}
    done: set = set()
    counter: int = 0
    heap: list = [(h(START), h(START), counter, START)]
    taken: list = []
    while heap:
        _f, _h, _k, c = heapq.heappop(heap)
        if c in done:
            continue
        done.add(c)
        taken.append(c)
        if c == GOAL:
            break
        for n in _neighbours(c, occ):
            ng: float = g[c] + cost[n]
            if n not in g or ng < g[n]:
                g[n] = ng
                parent[n] = c
                counter += 1
                heapq.heappush(heap, (ng + h(n), h(n), counter, n))
    return g, _path_back(parent, GOAL), taken


def path_cost(path: list, cost: np.ndarray) -> float:
    return float(sum(cost[c] for c in path[1:]))


# The small roadmap: six poses a person taught the arm, and the time in
# seconds to move directly between the pairs that have a clear straight move.
POSES: dict[str, tuple[float, float]] = {
    'home': (0.0, 2.0),
    'camera view': (2.2, 3.6),
    'above bin': (2.4, 0.4),
    'above scale': (4.8, 2.0),
    'above tray': (7.2, 3.6),
    'above chute': (7.2, 0.4),
}
MOVES: list[tuple[str, str, float]] = [
    ('home', 'camera view', 1.2),
    ('home', 'above bin', 1.5),
    ('camera view', 'above scale', 1.1),
    ('above bin', 'above scale', 0.9),
    ('camera view', 'above tray', 2.6),
    ('above scale', 'above tray', 1.4),
    ('above scale', 'above chute', 1.8),
    ('above bin', 'above chute', 3.6),
    ('above tray', 'above chute', 1.0),
]


def roadmap_dijkstra(start: str, goal: str) -> tuple[dict, dict, list[str], list[tuple[str, float]]]:
    """Dijkstra on the pose roadmap. Also returns the order poses were finalised in."""
    adj: dict[str, list[tuple[str, float]]] = {p: [] for p in POSES}
    for a, b, t in MOVES:
        adj[a].append((b, t))
        adj[b].append((a, t))
    best: dict[str, float] = {start: 0.0}
    parent: dict[str, str | None] = {start: None}
    heap: list = [(0.0, start)]
    done: list[tuple[str, float]] = []
    seen: set = set()
    while heap:
        d, p = heapq.heappop(heap)
        if p in seen:
            continue
        seen.add(p)
        done.append((p, round(d, 3)))
        if p == goal:
            break
        for q, t in adj[p]:
            if q not in best or d + t < best[q] - 1e-9:
                best[q] = d + t
                parent[q] = p
                heapq.heappush(heap, (d + t, q))
    path: list[str] = [goal]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])  # type: ignore[arg-type]
    return best, parent, path[::-1], done


# ==========================================================================
# PART 2: the two-joint arm and its configuration space
# ==========================================================================

L1: float = 3.0
L2: float = 2.0
Q1_RANGE: tuple[float, float] = (-180.0, 180.0)   # joint 1 limits, degrees
Q2_RANGE: tuple[float, float] = (-160.0, 160.0)   # joint 2 limits, degrees

# Three things on the table, all further than 3 m from the base, so only
# link 2 and the gripper can touch them: a box, a post and a jar.
BOX: tuple[float, float, float, float] = (0.3, 1.5, 3.4, 4.4)   # x0, x1, y0, y1
POSTS: list[tuple[float, float, float]] = [(3.3, 2.3, 0.5), (-3.7, 1.3, 0.5)]
OBST_COLOURS: list[str] = [GRIP, PURPLE, SLIDE]     # box, first post, second post
OBST_NAMES: list[str] = ['box', 'post', 'jar']

Q_START: np.ndarray = np.array([10.0, 20.0])
Q_GOAL: np.ndarray = np.array([130.0, 20.0])


def arm_points(q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Points every 5 cm along both links, for joint angles q (degrees, shape (..., 2))."""
    r: np.ndarray = np.radians(q)
    a: np.ndarray = r[..., 0]
    b: np.ndarray = a + r[..., 1]
    t1: np.ndarray = np.linspace(0, 1, 61)
    t2: np.ndarray = np.linspace(0, 1, 41)
    ex: np.ndarray = L1 * np.cos(a)
    ey: np.ndarray = L1 * np.sin(a)
    x = np.concatenate([np.multiply.outer(ex, t1),
                        ex[..., None] + np.multiply.outer(L2 * np.cos(b), t2)], -1)
    y = np.concatenate([np.multiply.outer(ey, t1),
                        ey[..., None] + np.multiply.outer(L2 * np.sin(b), t2)], -1)
    return x, y


def hits_each(q: np.ndarray, posts: list[tuple[float, float, float]] | None = None) -> np.ndarray:
    """For each configuration, which obstacle it hits: -1 none, 0 box, 1.. posts."""
    posts = POSTS if posts is None else posts
    x, y = arm_points(np.asarray(q, float))
    out: np.ndarray = np.full(x.shape[:-1], -1)
    inb = ((x >= BOX[0]) & (x <= BOX[1]) & (y >= BOX[2]) & (y <= BOX[3])).any(-1)
    out[inb] = 0
    for i, (cx, cy, rr) in enumerate(posts):
        inp = ((x - cx) ** 2 + (y - cy) ** 2 <= rr ** 2).any(-1)
        out[(out < 0) & inp] = i + 1
    return out


class Checker:
    """A collision checker that counts how many configurations it was asked about."""

    def __init__(self) -> None:
        self.calls: int = 0

    def free(self, q: np.ndarray) -> bool:
        self.calls += 1
        return bool(hits_each(q[None])[0] < 0)

    def edge_free(self, a: np.ndarray, b: np.ndarray, step: float = 1.0) -> bool:
        """Test points every `step` degrees along the straight joint-space line a-b."""
        n: int = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        pts: np.ndarray = a + np.linspace(0, 1, n + 1)[1:, None] * (b - a)
        self.calls += len(pts)
        return bool((hits_each(pts) < 0).all())


def _sample(rng: np.random.Generator) -> np.ndarray:
    return np.array([rng.uniform(*Q1_RANGE), rng.uniform(*Q2_RANGE)])


def _steer(a: np.ndarray, b: np.ndarray, step: float) -> np.ndarray:
    d: float = float(np.linalg.norm(b - a))
    return b.copy() if d <= step else a + (b - a) * (step / d)


def _tree_path(nodes: list, parent: list, i: int) -> list:
    out: list = []
    while i >= 0:
        out.append(nodes[i])
        i = parent[i]
    return out[::-1]


def rrt(seed: int, step: float = 8.0, goal_bias: float = 0.05,
        max_iter: int = 20000) -> dict:
    """Plain RRT from Q_START towards Q_GOAL. Returns the tree, the path and the counts."""
    rng: np.random.Generator = np.random.default_rng(seed)
    chk: Checker = Checker()
    nodes: list = [Q_START.copy()]
    parent: list = [-1]
    snapshots: dict = {}
    for it in range(1, max_iter + 1):
        target: np.ndarray = Q_GOAL if rng.random() < goal_bias else _sample(rng)
        dists: np.ndarray = np.linalg.norm(np.array(nodes) - target, axis=1)
        near: int = int(np.argmin(dists))
        new: np.ndarray = _steer(nodes[near], target, step)
        if chk.free(new) and chk.edge_free(nodes[near], new):
            nodes.append(new)
            parent.append(near)
            if np.linalg.norm(new - Q_GOAL) <= step and chk.edge_free(new, Q_GOAL):
                nodes.append(Q_GOAL.copy())
                parent.append(len(nodes) - 2)
                return {'nodes': nodes, 'parent': parent, 'iterations': it,
                        'checks': chk.calls, 'path': _tree_path(nodes, parent, len(nodes) - 1),
                        'snapshots': snapshots}
        if it in (40, 150):
            snapshots[it] = (list(nodes), list(parent))
    return {'nodes': nodes, 'parent': parent, 'iterations': max_iter, 'checks': chk.calls,
            'path': None, 'snapshots': snapshots}


def rrt_connect(seed: int, step: float = 8.0, max_iter: int = 20000) -> dict:
    """RRT-Connect: one tree from the start, one from the goal, taking turns."""
    rng: np.random.Generator = np.random.default_rng(seed)
    chk: Checker = Checker()
    trees: list = [([Q_START.copy()], [-1]), ([Q_GOAL.copy()], [-1])]

    def extend(tree: tuple, target: np.ndarray) -> tuple[str, int]:
        nodes, parent = tree
        near: int = int(np.argmin(np.linalg.norm(np.array(nodes) - target, axis=1)))
        new: np.ndarray = _steer(nodes[near], target, step)
        if chk.free(new) and chk.edge_free(nodes[near], new):
            nodes.append(new)
            parent.append(near)
            return ('reached' if np.allclose(new, target) else 'advanced'), len(nodes) - 1
        return 'trapped', -1

    a: int = 0
    for it in range(1, max_iter + 1):
        target: np.ndarray = _sample(rng)
        status, ia = extend(trees[a], target)
        if status != 'trapped':
            q_new: np.ndarray = trees[a][0][ia]
            while True:
                status2, ib = extend(trees[1 - a], q_new)
                if status2 != 'advanced':
                    break
            if status2 == 'reached':
                pa = _tree_path(trees[a][0], trees[a][1], ia)
                pb = _tree_path(trees[1 - a][0], trees[1 - a][1], ib)
                path = pa + pb[::-1][1:]
                if a == 1:
                    path = path[::-1]
                return {'trees': trees, 'iterations': it, 'checks': chk.calls, 'path': path}
        a = 1 - a
    return {'trees': trees, 'iterations': max_iter, 'checks': chk.calls, 'path': None}


def prm(seed: int, n: int = 150, k: int = 10, radius: float = 45.0) -> dict:
    """A probabilistic roadmap: n random samples, each joined to up to k free neighbours."""
    rng: np.random.Generator = np.random.default_rng(seed)
    chk: Checker = Checker()
    raw: list = [_sample(rng) for _ in range(n)]
    rejected: list = [q for q in raw if not chk.free(q)]
    nodes: list = [q for q in raw if hits_each(q[None])[0] < 0]
    build_checks_before_edges: int = chk.calls
    edges: set = set()
    arr: np.ndarray = np.array(nodes)

    def connect(i: int, pts: np.ndarray) -> None:
        d: np.ndarray = np.linalg.norm(pts - pts[i], axis=1)
        for j in np.argsort(d)[1:k + 1]:
            if d[j] > radius:
                break
            e = (min(i, int(j)), max(i, int(j)))
            if e not in edges and chk.edge_free(pts[i], pts[int(j)]):
                edges.add(e)

    for i in range(len(nodes)):
        connect(i, arr)
    build_checks: int = chk.calls
    build_edges: int = len(edges)
    # Answering a query: add the start and the goal, join them, search the graph.
    q_chk_before: int = chk.calls
    nodes_q: list = nodes + [Q_START.copy(), Q_GOAL.copy()]
    arr_q: np.ndarray = np.array(nodes_q)
    connect(len(nodes_q) - 2, arr_q)
    connect(len(nodes_q) - 1, arr_q)
    adj: dict = {i: [] for i in range(len(nodes_q))}
    for i, j in edges:
        w: float = float(np.linalg.norm(arr_q[i] - arr_q[j]))
        adj[i].append((j, w))
        adj[j].append((i, w))
    s, gi = len(nodes_q) - 2, len(nodes_q) - 1
    best: dict = {s: 0.0}
    par: dict = {s: None}
    heap: list = [(0.0, s)]
    seen: set = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in seen:
            continue
        seen.add(u)
        if u == gi:
            break
        for v, w in adj[u]:
            if v not in best or d + w < best[v]:
                best[v] = d + w
                par[v] = u
                heapq.heappush(heap, (d + w, v))
    path = None
    if gi in par:
        path = [gi]
        while par[path[-1]] is not None:
            path.append(par[path[-1]])
        path = [nodes_q[i] for i in path[::-1]]
    return {'nodes': nodes_q, 'rejected': rejected, 'edges': edges, 'path': path,
            'build_checks': build_checks, 'build_edges': build_edges,
            'sample_checks': build_checks_before_edges,
            'query_checks': chk.calls - q_chk_before}


def path_length(path: list) -> float:
    return float(sum(np.linalg.norm(b - a) for a, b in zip(path[:-1], path[1:])))


def shortcut(path: list, seed: int, tries: int = 200) -> list:
    """Shorten a path by joining two random points on it when the straight line is free."""
    rng: np.random.Generator = np.random.default_rng(seed)
    chk: Checker = Checker()
    p: list = [np.array(q) for q in path]
    for _ in range(tries):
        if len(p) < 3:
            break
        i, j = sorted(rng.choice(len(p), 2, replace=False))
        if j - i < 2:
            continue
        if chk.edge_free(p[i], p[j]):
            p = p[:i + 1] + p[j:]
    return p


def two_link_ik(x: float, y: float) -> list[np.ndarray]:
    """Both joint-angle answers (elbow one way and the other) for a gripper point."""
    c2: float = (x * x + y * y - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    out: list[np.ndarray] = []
    for s in (1, -1):
        q2: float = s * np.arccos(np.clip(c2, -1, 1))
        q1: float = np.arctan2(y, x) - np.arctan2(L2 * np.sin(q2), L1 + L2 * np.cos(q2))
        out.append(np.degrees([q1, q2]))
    return out


def c_space_grid(res: float = 1.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    q1: np.ndarray = np.arange(Q1_RANGE[0], Q1_RANGE[1] + res / 2, res)
    q2: np.ndarray = np.arange(Q2_RANGE[0], Q2_RANGE[1] + res / 2, res)
    Q: np.ndarray = np.stack(np.meshgrid(q1, q2, indexing='ij'), -1)
    return q1, q2, hits_each(Q)


# ==========================================================================
# drawing helpers for the arm pictures
# ==========================================================================

def _draw_table_objects(ax: Axes, alpha: float = 1.0) -> None:
    ax.add_patch(Rectangle((BOX[0], BOX[2]), BOX[1] - BOX[0], BOX[3] - BOX[2],
                           facecolor=OBST_COLOURS[0], edgecolor='none', alpha=0.85 * alpha))
    for i, (cx, cy, r) in enumerate(POSTS):
        ax.add_patch(Circle((cx, cy), r, facecolor=OBST_COLOURS[i + 1], edgecolor='none',
                            alpha=0.85 * alpha))


def _draw_arm(ax: Axes, q: np.ndarray, colour: str = LINK, alpha: float = 1.0,
              lw: float = 6, joints: bool = True) -> None:
    a: float = np.radians(q[0])
    b: float = a + np.radians(q[1])
    e = (L1 * np.cos(a), L1 * np.sin(a))
    t = (e[0] + L2 * np.cos(b), e[1] + L2 * np.sin(b))
    ax.plot([0, e[0], t[0]], [0, e[1], t[1]], color=colour, lw=lw, alpha=alpha,
            solid_capstyle='round', zorder=4)
    if joints:
        ax.plot([0, e[0]], [0, e[1]], 'o', color=JOINT, ms=lw + 2, alpha=alpha, zorder=5)
        ax.plot([t[0]], [t[1]], 'o', color=INK, ms=lw - 1, alpha=alpha, zorder=5)


def _tip(q: np.ndarray) -> tuple[float, float]:
    a: float = np.radians(q[0])
    b: float = a + np.radians(q[1])
    return (L1 * np.cos(a) + L2 * np.cos(b), L1 * np.sin(a) + L2 * np.sin(b))


def _draw_c_space(ax: Axes, labels: bool = True, pale: bool = False) -> None:
    q1, q2, H = c_space_grid(1.0)
    img: np.ndarray = np.ones(H.shape + (3,))
    for i, col in enumerate(OBST_COLOURS):
        rgb = matplotlib.colors.to_rgb(col)
        if pale:
            rgb = tuple(0.55 + 0.45 * c for c in rgb)
        img[H == i] = rgb
    ax.imshow(np.transpose(img, (1, 0, 2)), origin='lower',
              extent=(q1[0] - 0.5, q1[-1] + 0.5, q2[0] - 0.5, q2[-1] + 0.5),
              interpolation='nearest', zorder=0)
    ax.set_xlim(*Q1_RANGE)
    ax.set_ylim(*Q2_RANGE)
    ax.set_aspect('equal')
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-150, 151, 50))
    ax.tick_params(labelsize=9, colors=MUTED)
    for s in ax.spines.values():
        s.set_color(GRID)
    if labels:
        ax.set_xlabel('joint 1 angle q1 (degrees)', fontsize=10, color=INK)
        ax.set_ylabel('joint 2 angle q2 (degrees)', fontsize=10, color=INK)


def _mark(ax: Axes, q: np.ndarray, text: str, colour: str, dx: float, dy: float) -> None:
    ax.plot(*q, 'o', color=colour, ms=9, mec='white', mew=1.5, zorder=8)
    ax.annotate(text, q, xytext=(q[0] + dx, q[1] + dy), fontsize=10, color=INK,
                ha='center', va='center', zorder=9,
                bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=GRID))


# ==========================================================================
# overview pictures
# ==========================================================================

def one_move_three_jobs() -> None:
    """Workspace: the target and its two IK answers. C-space: raw path, then shortened."""
    target: tuple[float, float] = _tip(Q_GOAL)
    iks: list[np.ndarray] = two_link_ik(*target)
    raw = rrt_connect(seed=3)['path']
    short = shortcut(raw, seed=1)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.6), facecolor='white',
                                 gridspec_kw={'width_ratios': [1, 1.15]})
    _axes(a1, (-5.6, 5.6), (-1.6, 5.8))
    a1.axhline(0, color=GRID, lw=1, zorder=0)
    _draw_table_objects(a1)
    _draw_arm(a1, Q_START, LINK)
    for q, col in zip(iks, (WRIST, INK)):
        _draw_arm(a1, q, col, alpha=0.5, lw=5)
    a1.text(-1.5, 2.75, 'A', fontsize=11, color=WRIST, weight='bold', ha='center')
    a1.text(-2.35, 1.15, 'B', fontsize=11, color=INK, weight='bold', ha='center')
    a1.plot(*target, marker='*', color=INK, ms=16, zorder=7)
    a1.text(target[0], target[1] + 0.7, 'target for the gripper', fontsize=10,
            ha='center', color=INK)
    a1.text(_tip(Q_START)[0], _tip(Q_START)[1] - 0.75, 'arm now', fontsize=10, ha='center',
            color=LINK)
    a1.text(-0.2, -1.0, 'base', fontsize=10, ha='center', color=MUTED)
    a1.text(-5.4, -0.6, 'A and B: two sets of joint angles\nthat both reach the target',
            fontsize=10, color=INK, va='top')
    _title(a1, '1. Inverse kinematics: target to joint angles')

    _draw_c_space(a2, pale=True)
    rp = np.array(raw)
    sp = np.array(short)
    a2.plot(rp[:, 0], rp[:, 1], '-', color=MUTED, lw=1.5, zorder=3,
            label=f'path the planner found ({path_length(raw):.0f}°)')
    a2.plot(sp[:, 0], sp[:, 1], '-', color=LINK, lw=3, zorder=4,
            label=f'the same path shortened ({path_length(short):.0f}°)')
    _mark(a2, Q_START, 'arm now', LINK, 0, -28)
    _mark(a2, iks[0], 'A', WRIST, -12, -20)
    _mark(a2, iks[1], 'B', INK, 0, -28)
    a2.legend(loc='upper left', fontsize=9, framealpha=0.95)
    _title(a2, '2. Search finds a free path, 3. shortening tidies it')
    fig.tight_layout(w_pad=3)
    _save(fig, 'overview', 'one-move-three-jobs.svg')


def cells_per_joint() -> None:
    """How many grid cells a joint space has at 10 degree steps, for 1 to 7 joints."""
    joints: np.ndarray = np.arange(1, 8)
    cells: np.ndarray = 36.0 ** joints
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor='white')
    bars = ax.bar(joints, cells, color=[LINK if j <= 3 else GRIP for j in joints], width=0.6)
    ax.set_yscale('log')
    ax.set_ylim(1, 1e13)
    ax.set_xticks(joints)
    ax.set_xlabel('number of joints', fontsize=11, color=INK)
    ax.set_ylabel('grid cells at 10° steps (log scale)', fontsize=11, color=INK)
    for b, c in zip(bars, cells):
        m, e = f'{c:.1e}'.split('e+')
        txt = f'{int(c):,}' if c < 1e7 else rf'${m} \times 10^{{{int(e)}}}$'
        ax.text(b.get_x() + b.get_width() / 2, c * 2.2, txt, ha='center', fontsize=9,
                color=INK)
    ax.text(0.7, 3e11, 'blue: few enough cells to search them all\n'
            'red: millions of cells or more, each needing a collision check;\n'
            'arms with this many joints use sampling', fontsize=10, color=INK, va='top')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=10, colors=INK)
    ax.set_title('Every extra joint multiplies the cells by 36', fontsize=12, weight='bold',
                 color=INK, pad=10)
    fig.tight_layout()
    _save(fig, 'overview', 'cells-per-joint.svg')


# ==========================================================================
# graph search pictures
# ==========================================================================

def _draw_grid(ax: Axes, occ: np.ndarray, shade: dict | None = None) -> None:
    _axes(ax, (-0.1, GW + 0.1), (-0.1, GH + 0.1))
    for x in range(GW):
        for y in range(GH):
            fc = OBST if occ[x, y] else (shade.get((x, y), 'white') if shade else 'white')
            ax.add_patch(Rectangle((x, y), 1, 1, facecolor=fc, edgecolor=GRID, lw=0.8))


def _draw_path(ax: Axes, path: list, colour: str = LINK, under_text: bool = False) -> None:
    p = np.array(path) + 0.5
    if under_text:
        ax.plot(p[:, 0], p[:, 1], '-', color=colour, lw=9, alpha=0.35, zorder=5,
                solid_capstyle='round')
    else:
        ax.plot(p[:, 0], p[:, 1], '-', color=colour, lw=3.5, zorder=6, solid_capstyle='round')


def _start_goal(ax: Axes) -> None:
    for c, t, col in ((START, 'S', SLIDE), (GOAL, 'G', GRIP)):
        ax.add_patch(Circle((c[0] + 0.5, c[1] + 0.5), 0.36, facecolor=col, edgecolor='white',
                            lw=1.5, zorder=8))
        ax.text(c[0] + 0.5, c[1] + 0.5, t, ha='center', va='center', color='white',
                fontsize=10, weight='bold', zorder=9)


def roadmap_picture() -> None:
    best, parent, path, _done = roadmap_dijkstra('home', 'above chute')
    fig, ax = plt.subplots(figsize=(11, 5.2), facecolor='white')
    _axes(ax, (-1.2, 8.6), (-0.6, 4.6))
    on_path = {(a, b) for a, b in zip(path[:-1], path[1:])}
    on_path |= {(b, a) for a, b in on_path}
    for a, b, t in MOVES:
        pa, pb = POSES[a], POSES[b]
        hot = (a, b) in on_path
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], '-', color=LINK if hot else GRID,
                lw=4 if hot else 2.5, zorder=1)
        mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        ax.text(mx, my, f'{t:.1f} s', ha='center', va='center', fontsize=10,
                color=LINK if hot else MUTED, zorder=3,
                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none'))
    for name, (x, y) in POSES.items():
        col = SLIDE if name == 'home' else (GRIP if name == 'above chute' else JOINT)
        ax.add_patch(Circle((x, y), 0.2, facecolor=col, edgecolor='white', lw=1.5, zorder=4))
        dy = 0.48 if y > 1 else -0.5
        ax.text(x, y + dy, f'{name}\nbest {best[name]:.1f} s' if name in best else name,
                ha='center', va='center', fontsize=10, color=INK, zorder=5)
    ax.set_title('Dijkstra on six taught poses: fastest move from home to above chute',
                 fontsize=12, weight='bold', color=INK)
    _save(fig, 'graph-search', 'roadmap-of-poses.svg')


def bfs_waves() -> None:
    occ = grid_map()
    steps, path, _taken = bfs(occ)
    fig, ax = plt.subplots(figsize=(11, 7.2), facecolor='white')
    maxs = max(steps.values())
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list('w', ['#fff4d6', '#f3c46b'])
    shade = {c: matplotlib.colors.to_hex(cmap(s / maxs)) for c, s in steps.items()}
    _draw_grid(ax, occ, shade)
    for (x, y), s in steps.items():
        if (x, y) in (START, GOAL):
            continue
        ax.text(x + 0.5, y + 0.5, str(s), ha='center', va='center', fontsize=8.5,
                color=INK, zorder=7)
    _draw_path(ax, path, under_text=True)
    _start_goal(ax)
    ax.set_title(f'Breadth-first search: the number is the fewest steps from S '
                 f'(G is {steps[GOAL]} steps)', fontsize=12, weight='bold', color=INK)
    _save(fig, 'graph-search', 'breadth-first-waves.svg')


def dijkstra_vs_astar() -> None:
    occ = grid_map()
    cost = np.ones((GW, GH))
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), facecolor='white')
    for ax, use_h, name in ((axes[0], False, 'Dijkstra'), (axes[1], True, 'A*')):
        g, path, taken = best_first(occ, cost, use_h)
        shade = {c: EXPANDED for c in taken}
        _draw_grid(ax, occ, shade)
        _draw_path(ax, path)
        _start_goal(ax)
        _title(ax, f'{name}: looked at {len(taken)} cells, path {g[GOAL]:.0f} steps')
    fig.tight_layout(w_pad=3)
    _save(fig, 'graph-search', 'dijkstra-and-a-star.svg')


def clearance_cost() -> None:
    occ = grid_map()
    cost = enter_cost(occ, 5.0)
    _s, bpath, _t = bfs(occ)
    g, dpath, _t2 = best_first(occ, cost, False)
    shade = {(x, y): COSTLY for x in range(GW) for y in range(GH)
             if cost[x, y] > 1 and not occ[x, y]}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), facecolor='white')
    for ax, path, name in ((axes[0], bpath, 'Fewest steps'), (axes[1], dpath, 'Lowest cost')):
        _draw_grid(ax, occ, shade)
        _draw_path(ax, path, LINK if name == 'Lowest cost' else WRIST)
        _start_goal(ax)
        _title(ax, f'{name}: {len(path) - 1} steps, cost {path_cost(path, cost):.0f}')
    fig.tight_layout(w_pad=3)
    _save(fig, 'graph-search', 'cost-keeps-clear.svg')


# ==========================================================================
# sampling-based planning pictures
# ==========================================================================

def workspace_and_c_space() -> None:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.6), facecolor='white',
                                 gridspec_kw={'width_ratios': [1, 1.15]})
    _axes(a1, (-5.6, 5.6), (-1.6, 5.8))
    a1.axhline(0, color=GRID, lw=1, zorder=0)
    _draw_table_objects(a1)
    _draw_arm(a1, Q_START, LINK)
    _draw_arm(a1, Q_GOAL, LINK, alpha=0.4)
    a1.text(_tip(Q_START)[0], _tip(Q_START)[1] - 0.7, 'start', fontsize=10, ha='center',
            color=INK)
    a1.text(_tip(Q_GOAL)[0], _tip(Q_GOAL)[1] + 0.6, 'goal', fontsize=10, ha='center',
            color=INK)
    lab = [((BOX[0] + BOX[1]) / 2, BOX[3] + 0.4, 'box'),
           (POSTS[0][0] + 0.95, POSTS[0][1], 'post'),
           (POSTS[1][0], POSTS[1][1] - 0.85, 'jar')]
    for x, y, t in lab:
        a1.text(x, y, t, fontsize=10, ha='center', va='center', color=INK)
    _title(a1, 'The table, seen from above')

    _draw_c_space(a2)
    line = np.array([Q_START, Q_GOAL])
    a2.plot(line[:, 0], line[:, 1], '--', color=INK, lw=1.5, zorder=3)
    _mark(a2, Q_START, 'start', LINK, -2, -26)
    _mark(a2, Q_GOAL, 'goal', LINK, 0, -26)
    for i, (x, y) in enumerate([(78, 112), (-22, 100), (158, -100)]):
        a2.text(x, y, OBST_NAMES[i], fontsize=10, ha='center', va='center',
                color=OBST_COLOURS[i], weight='bold',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none'))
    _title(a2, 'The same scene as joint angles (configuration space)')
    fig.tight_layout(w_pad=3)
    _save(fig, 'sampling-based-planning', 'workspace-and-configuration-space.svg')


def _draw_tree(ax: Axes, nodes: list, parent: list, colour: str) -> None:
    for i, p in enumerate(parent):
        if p >= 0:
            ax.plot([nodes[p][0], nodes[i][0]], [nodes[p][1], nodes[i][1]], '-',
                    color=colour, lw=0.9, zorder=2)
    arr = np.array(nodes)
    ax.plot(arr[:, 0], arr[:, 1], '.', color=colour, ms=2.5, zorder=2)


def rrt_growth() -> None:
    r = rrt(seed=7)
    c = rrt_connect(seed=7)
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.4), facecolor='white')
    n40, p40 = r['snapshots'][40]
    panels = [
        (axes[0], f'RRT after 40 tries: {len(n40)} points in the tree'),
        (axes[1], f'RRT at success: {r["iterations"]} tries, {len(r["nodes"])} points'),
        (axes[2], f'RRT-Connect at success: {c["iterations"]} tries, '
                  f'{len(c["trees"][0][0]) + len(c["trees"][1][0])} points'),
    ]
    for i, (ax, t) in enumerate(panels):
        _draw_c_space(ax, labels=(i == 0), pale=True)
        if i == 0:
            _draw_tree(ax, n40, p40, LINK)
        elif i == 1:
            _draw_tree(ax, r['nodes'], r['parent'], LINK)
            pp = np.array(r['path'])
            ax.plot(pp[:, 0], pp[:, 1], '-', color=INK, lw=2.5, zorder=5)
        else:
            _draw_tree(ax, *c['trees'][0], LINK)
            _draw_tree(ax, *c['trees'][1], WRIST)
            pp = np.array(c['path'])
            ax.plot(pp[:, 0], pp[:, 1], '-', color=INK, lw=2.5, zorder=5)
        _mark(ax, Q_START, 'start', LINK, -2, -26)
        _mark(ax, Q_GOAL, 'goal', WRIST if i == 2 else LINK, 0, -26)
        ax.set_title(t, fontsize=11, weight='bold', color=INK, pad=8)
    fig.tight_layout(w_pad=2)
    _save(fig, 'sampling-based-planning', 'rrt-and-rrt-connect.svg')


def prm_picture() -> None:
    res = prm(seed=5)
    nodes = res['nodes']
    fig, ax = plt.subplots(figsize=(9.5, 6.4), facecolor='white')
    _draw_c_space(ax, pale=True)
    for i, j in res['edges']:
        ax.plot([nodes[i][0], nodes[j][0]], [nodes[i][1], nodes[j][1]], '-', color=LINK_PALE,
                lw=1.1, zorder=2)
    arr = np.array(nodes[:-2])
    ax.plot(arr[:, 0], arr[:, 1], 'o', color=LINK, ms=3.5, zorder=3)
    rej = np.array(res['rejected'])
    ax.plot(rej[:, 0], rej[:, 1], 'x', color=INK, ms=6, mew=1.5, zorder=3)
    pp = np.array(res['path'])
    ax.plot(pp[:, 0], pp[:, 1], '-', color=INK, lw=2.5, zorder=5)
    _mark(ax, Q_START, 'start', LINK, -2, -26)
    _mark(ax, Q_GOAL, 'goal', LINK, 0, -26)
    ax.set_title(f'PRM: {len(nodes) - 2} free samples, {res["build_edges"]} free edges, '
                 f'{len(res["rejected"])} samples rejected (×)',
                 fontsize=11, weight='bold', color=INK, pad=8)
    fig.tight_layout()
    _save(fig, 'sampling-based-planning', 'probabilistic-roadmap.svg')


# A thin rod standing where the gripper passes, used only by the edge-check picture.
THIN: tuple[float, float, float] = (0.0, 0.0, 0.06)
EDGE_A: np.ndarray = np.array([0.0, 30.0])
EDGE_B: np.ndarray = np.array([60.0, 30.0])


def thin_rod() -> tuple[float, float, float]:
    """A 6 cm rod on the gripper's arc, halfway between the 40 and 50 degree checks."""
    x, y = _tip(np.array([45.0, 30.0]))
    return (x, y, THIN[2])


def edge_checks(step: float) -> tuple[np.ndarray, np.ndarray]:
    """The configurations checked along EDGE_A to EDGE_B, and whether each hits the rod."""
    n: int = int(np.ceil(np.linalg.norm(EDGE_B - EDGE_A) / step))
    pts: np.ndarray = EDGE_A + np.linspace(0, 1, n + 1)[:, None] * (EDGE_B - EDGE_A)
    return pts, hits_each(pts, posts=[thin_rod()]) == 1


def edge_check_picture() -> None:
    rod = thin_rod()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), facecolor='white')
    for ax, step in zip(axes, (10.0, 1.0)):
        _axes(ax, (-0.8, 5.4), (-0.8, 5.4))
        pts, hit = edge_checks(step)
        # the area the arm sweeps through, drawn as many faint arms
        for q in EDGE_A + np.linspace(0, 1, 61)[:, None] * (EDGE_B - EDGE_A):
            _draw_arm(ax, q, LINK_PALE, alpha=0.5, lw=2, joints=False)
        shown = pts if step >= 5 else pts[::5]
        for q in shown:
            _draw_arm(ax, q, LINK, alpha=0.9, lw=2.5, joints=False)
        for q, h in zip(pts, hit):
            if h:
                _draw_arm(ax, q, GRIP, alpha=1.0, lw=3, joints=False)
        ax.add_patch(Circle(rod[:2], rod[2] * 2.2, facecolor=INK, edgecolor='none', zorder=8))
        ax.annotate('thin rod, 12 cm across\n(drawn larger)', rod[:2], xytext=(rod[0] + 1.5, rod[1] + 0.9),
                    fontsize=10, color=INK, ha='center', zorder=9,
                    arrowprops=dict(arrowstyle='->', color=INK, lw=1))
        ax.plot(0, 0, 'o', color=JOINT, ms=9, zorder=9)
        n_hit = int(hit.sum())
        verdict = ('edge passes, rod missed' if n_hit == 0 else
                   f'{n_hit} check{"s" if n_hit > 1 else ""} hit{"" if n_hit > 1 else "s"}, '
                   'edge rejected')
        _title(ax, f'Checked every {step:.0f}°: {len(pts)} checks, {verdict}', 11)
        if step < 5:
            ax.text(2.6, -0.55, 'dark blue: every 5th check drawn; red: checks that hit',
                    fontsize=9, color=MUTED, ha='center')
    fig.tight_layout(w_pad=3)
    _save(fig, 'sampling-based-planning', 'checking-an-edge.svg')


# --------------------------------------------------------------------------

def print_numbers() -> None:
    """Print every number the documents quote."""
    occ = grid_map()
    print('free cells', int((~occ).sum()), 'of', occ.size)
    steps, bpath, btaken = bfs(occ)
    print('BFS: steps to goal', steps[GOAL], 'taken off list', len(btaken), 'reached', len(steps))
    one = np.ones((GW, GH))
    g, dp, dt = best_first(occ, one, False)
    print('Dijkstra uniform: cost', g[GOAL], 'taken', len(dt))
    g, ap, at = best_first(occ, one, True)
    print('A* uniform: cost', g[GOAL], 'taken', len(at))
    cost = enter_cost(occ, 5.0)
    print('BFS path in clearance costs: steps', len(bpath) - 1, 'cost', path_cost(bpath, cost))
    g, dp, dt = best_first(occ, cost, False)
    print('Dijkstra clearance: steps', len(dp) - 1, 'cost', g[GOAL], 'taken', len(dt))
    g, ap, at = best_first(occ, cost, True)
    print('A* clearance: steps', len(ap) - 1, 'cost', g[GOAL], 'taken', len(at))
    best, parent, path, done = roadmap_dijkstra('home', 'above chute')
    print('roadmap path', path, 'best', best)
    print('roadmap finalised order', done)

    q1, q2, H = c_space_grid(1.0)
    print('c-space cells', H.size, 'blocked fraction', round(float((H >= 0).mean()), 4),
          'per obstacle', [round(float((H == i).mean()), 4) for i in range(3)])
    print('start tip', np.round(_tip(Q_START), 3), 'goal tip', np.round(_tip(Q_GOAL), 3))
    chk = Checker()
    print('straight line free?', chk.edge_free(Q_START, Q_GOAL), 'checks', chk.calls)
    r = rrt(seed=7)
    print('RRT seed 7: iterations', r['iterations'], 'nodes', len(r['nodes']), 'checks',
          r['checks'], 'path len', round(path_length(r['path']), 1), 'waypoints', len(r['path']))
    c = rrt_connect(seed=7)
    print('RRT-Connect seed 7: iterations', c['iterations'], 'nodes',
          len(c['trees'][0][0]) + len(c['trees'][1][0]), 'checks', c['checks'],
          'path len', round(path_length(c['path']), 1))
    s = shortcut(c['path'], seed=1)
    print('shortcut of RRT-Connect seed 7:', round(path_length(s), 1), 'waypoints', len(s))
    p = prm(seed=5)
    print('PRM seed 5: free', len(p['nodes']) - 2, 'rejected', len(p['rejected']), 'edges',
          p['build_edges'], 'build checks', p['build_checks'], 'query checks',
          p['query_checks'], 'path len', round(path_length(p['path']), 1))
    for name, fn in (('RRT', lambda sd: rrt(sd)), ('RRT-Connect', lambda sd: rrt_connect(sd))):
        its, cks, lens = [], [], []
        for sd in range(100):
            res = fn(sd)
            its.append(res['iterations'])
            cks.append(res['checks'])
            lens.append(path_length(res['path']))
        its, cks, lens = map(np.array, (its, cks, lens))
        print(name, '100 seeds: tries median', np.median(its), 'p90', np.percentile(its, 90),
              'min', its.min(), 'max', its.max(), '| checks median', np.median(cks), 'max',
              cks.max(), '| length min', round(lens.min()), 'median', round(np.median(lens)),
              'max', round(lens.max()))
    for step in (10.0, 1.0):
        pts, hit = edge_checks(step)
        print('edge check step', step, 'checks', len(pts), 'hits', int(hit.sum()))
    iks = two_link_ik(*_tip(Q_GOAL))
    print('IK answers for goal tip', [np.round(q, 1) for q in iks])
    print('grid cells at 10 deg', [36 ** j for j in range(1, 8)])


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 2 and sys.argv[1] == '--numbers':
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    one_move_three_jobs()
    cells_per_joint()
    roadmap_picture()
    bfs_waves()
    dijkstra_vs_astar()
    clearance_cost()
    workspace_and_c_space()
    rrt_growth()
    prm_picture()
    edge_check_picture()


if __name__ == '__main__':
    main()
