"""Generate the diagrams for the collision, constraint and sampling-optimisation parts
of docs/05_programming-techniques/06_planning-and-search/.

This covers two documents:

- 02_most-used/01_sampling-based-planning.md, its two sections "How a collision
  checker answers" and "Planning with rules on the way". Their pictures go to
  docs/images/planning-and-search/sampling-based-planning/.
- 03_also-used/02_sampling-based-optimisation-and-mpc.md. Its pictures go to
  docs/images/planning-and-search/sampling-based-optimisation-and-mpc/.

Run with:  pixi run python ../docs/diagrams/planning_and_search_4.py
Add --png <dir> to also write PNG copies for checking.
Run with --numbers to print every number the documents quote.

Every picture that shows an algorithm's result is the real result. The script
runs bounding-box tests, a bounding-volume tree, the GJK distance algorithm,
conservative advancement along a joint move, RRT with and without a "keep the cup
upright" rule, projection onto a rule, and random shooting, the cross-entropy
method, CMA-ES and model predictive control on a block-pushing model. It uses
numpy only. The random parts use fixed seeds, so the pictures and numbers are the
same every time.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle  # noqa: E402
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
TABLE: str = '#eadfcb'
PURPLE: str = '#8e5bb5'
PALE_GREY: str = '#e6e6e6'

SBP: str = 'sampling-based-planning'
SOM: str = 'sampling-based-optimisation-and-mpc'


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


def _plain_axes(ax: Axes) -> None:
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=10)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


# ==========================================================================
# PART 1: how a collision checker answers
# ==========================================================================

# The book's two-joint arm, seen from above: link 1 is 3 m, link 2 is 2 m.
L1: float = 3.0
L2: float = 2.0
LINK_WIDTH: float = 0.3         # each link drawn as a bar 30 cm wide
BOX: tuple[float, float, float, float] = (0.3, 1.5, 3.4, 4.4)   # x0, x1, y0, y1
POSTS: list[tuple[float, float, float]] = [(3.3, 2.3, 0.5), (-3.7, 1.3, 0.5)]
OBST_COLOURS: list[str] = [GRIP, PURPLE, SLIDE]
OBST_NAMES: list[str] = ['box', 'post', 'jar']


def _elbow_tip(q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a: float = np.radians(q[0])
    b: float = a + np.radians(q[1])
    e = np.array([L1 * np.cos(a), L1 * np.sin(a)])
    t = e + np.array([L2 * np.cos(b), L2 * np.sin(b)])
    return e, t


def link_rectangles(q: np.ndarray) -> list[np.ndarray]:
    """The two links as 4-corner rectangles, LINK_WIDTH wide."""
    e, t = _elbow_tip(q)
    out: list[np.ndarray] = []
    for p0, p1 in ((np.zeros(2), e), (e, t)):
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        n = np.array([-d[1], d[0]]) * LINK_WIDTH / 2
        out.append(np.array([p0 + n, p1 + n, p1 - n, p0 - n]))
    return out


def aabb(pts: np.ndarray) -> tuple[float, float, float, float]:
    return (float(pts[:, 0].min()), float(pts[:, 0].max()),
            float(pts[:, 1].min()), float(pts[:, 1].max()))


def boxes_overlap(a: tuple, b: tuple) -> bool:
    return a[0] <= b[1] and b[0] <= a[1] and a[2] <= b[3] and b[2] <= a[3]


def obstacle_aabbs() -> list[tuple[float, float, float, float]]:
    out = [BOX]
    for cx, cy, r in POSTS:
        out.append((cx - r, cx + r, cy - r, cy + r))
    return out


def spheres_for_rect(rect: np.ndarray, n: int) -> tuple[np.ndarray, float]:
    """n circles along a rectangle's middle line that together cover the rectangle."""
    p0 = (rect[0] + rect[3]) / 2
    p1 = (rect[1] + rect[2]) / 2
    length = np.linalg.norm(p1 - p0)
    seg = length / n
    centres = p0 + (np.arange(n)[:, None] + 0.5) / n * (p1 - p0)
    r = float(np.hypot(seg / 2, LINK_WIDTH / 2))
    return centres, r


BV_Q: np.ndarray = np.array([10.0, 30.0])


def rect_circle_gap(rect: np.ndarray, cx: float, cy: float, r: float) -> float:
    """The exact gap between a rectangle and a circle; 0 or less means they touch."""
    c = np.array([cx, cy])
    sides = [float((rect[(i + 1) % 4] - rect[i])[0] * (c - rect[i])[1]
                   - (rect[(i + 1) % 4] - rect[i])[1] * (c - rect[i])[0]) for i in range(4)]
    if all(v <= 0 for v in sides) or all(v >= 0 for v in sides):
        return -r
    return min(_point_seg_dist(c, rect[i], rect[(i + 1) % 4]) for i in range(4)) - r


def broad_phase() -> list[tuple[int, int, bool, float | None]]:
    """For each (link, obstacle) pair: do their axis-aligned boxes overlap, and if so, the exact gap."""
    rects = link_rectangles(BV_Q)
    out = []
    for i, r in enumerate(rects):
        for j, ob in enumerate(obstacle_aabbs()):
            ov = boxes_overlap(aabb(r), ob)
            gap = rect_circle_gap(r, *POSTS[j - 1]) if (ov and j > 0) else None
            out.append((i, j, ov, gap))
    return out


# ---- a bounding-volume tree over a mug's outline -------------------------

def mug_segments() -> np.ndarray:
    """A mug seen from above, as 64 short straight edges: a round body and a handle loop."""
    body_n, handle_n = 48, 16
    th = np.linspace(0, 2 * np.pi, body_n + 1)
    body = np.stack([4.0 * np.cos(th), 4.0 * np.sin(th)], 1)
    segs = [np.array([body[i], body[i + 1]]) for i in range(body_n)]
    # the handle: a flattened loop on the right-hand side, from about 4 to 6.5 cm
    ph = np.linspace(-np.pi / 2, np.pi / 2, handle_n // 2 + 1)
    outer = np.stack([4.0 + 2.5 * np.cos(ph), 2.0 * np.sin(ph)], 1)
    inner = np.stack([4.0 + 1.5 * np.cos(ph[::-1]), 1.2 * np.sin(ph[::-1])], 1)
    for pts in (outer, inner):
        for i in range(len(pts) - 1):
            segs.append(np.array([pts[i], pts[i + 1]]))
    return np.array(segs)


class BVNode:
    def __init__(self, idx: np.ndarray, segs: np.ndarray, depth: int) -> None:
        pts = segs[idx].reshape(-1, 2)
        self.box = aabb(pts)
        self.idx = idx
        self.depth = depth
        self.kids: list[BVNode] = []
        if len(idx) > 2:
            mid = segs[idx].mean(1)
            w = self.box[1] - self.box[0]
            h = self.box[3] - self.box[2]
            axis = 0 if w >= h else 1
            order = idx[np.argsort(mid[:, axis], kind='stable')]
            half = len(order) // 2
            self.kids = [BVNode(order[:half], segs, depth + 1), BVNode(order[half:], segs, depth + 1)]


def _box_circle_gap(box: tuple, c: np.ndarray) -> float:
    dx = max(box[0] - c[0], 0.0, c[0] - box[1])
    dy = max(box[2] - c[1], 0.0, c[1] - box[3])
    return float(np.hypot(dx, dy))


def _point_seg_dist(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
    return float(np.linalg.norm(p - (a + t * ab)))


FINGER: tuple[float, float, float] = (5.2, -3.4, 0.6)     # a fingertip near the mug: x, y, radius (cm)


def bv_query(root: BVNode, segs: np.ndarray, c: np.ndarray, r: float) -> dict:
    """Does a circle touch any edge? Walk the tree, opening only boxes the circle touches."""
    visited: list[BVNode] = []
    tested: list[int] = []
    hit = False
    stack = [root]
    while stack:
        n = stack.pop()
        visited.append(n)
        if _box_circle_gap(n.box, c) > r:
            continue
        if not n.kids:
            for i in n.idx:
                tested.append(int(i))
                if _point_seg_dist(c, segs[i, 0], segs[i, 1]) <= r:
                    hit = True
            continue
        stack.extend(n.kids)
    return {'visited': visited, 'tested': tested, 'hit': hit}


def _all_nodes(n: BVNode) -> list[BVNode]:
    out = [n]
    for k in n.kids:
        out += _all_nodes(k)
    return out


# ---- GJK: the distance between two convex shapes -------------------------

def rot(deg: float) -> np.ndarray:
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


# A gripper finger (a 2 x 6 cm bar, turned 20 degrees) and a jar (a hexagon, 4 cm across the corners).
FINGER_SHAPE: np.ndarray = (np.array([[-1.0, -3.0], [1.0, -3.0], [1.0, 3.0], [-1.0, 3.0]]) @ rot(20).T)
JAR_SHAPE: np.ndarray = np.array([[4 * np.cos(t), 4 * np.sin(t)] for t in np.radians(np.arange(0, 360, 60) + 15)])
FINGER_APART: np.ndarray = np.array([-3.0, 1.0])
JAR_AT: np.ndarray = np.array([4.0, 0.0])
FINGER_OVERLAP: np.ndarray = np.array([0.4, 0.8])


def _support(P: np.ndarray, d: np.ndarray) -> int:
    return int(np.argmax(P @ d))


def gjk(A: np.ndarray, B: np.ndarray, max_iter: int = 30) -> dict:
    """The GJK distance algorithm in 2D, for convex polygons A and B.

    It works on the difference shape A - B: every point of A minus every point of
    B. The shapes touch exactly when that shape contains the origin, and the
    distance between them is the distance from the origin to that shape. GJK
    looks for the point of the difference shape nearest the origin, using a
    'simplex' of at most three of its corners.
    """
    def w_of(ia: int, ib: int) -> np.ndarray:
        return A[ia] - B[ib]

    simplex: list[tuple[int, int]] = [(_support(A, np.array([1.0, 0])), _support(B, np.array([-1.0, 0])))]
    lam = np.array([1.0])
    v = w_of(*simplex[0])
    history: list[dict] = []
    for _ in range(max_iter):
        history.append({'simplex': list(simplex), 'v': v.copy()})
        if np.dot(v, v) < 1e-12:
            return {'dist': 0.0, 'history': history, 'touch': True}
        d = -v
        new = (_support(A, d), _support(B, -d))
        w = w_of(*new)
        if np.dot(v, v) - np.dot(v, w) < 1e-9:
            break
        simplex.append(new)
        pts = np.array([w_of(*s) for s in simplex])
        v, keep, lam = _closest_on_simplex(pts)
        if keep is None:
            history.append({'simplex': list(simplex), 'v': np.zeros(2)})
            return {'dist': 0.0, 'history': history, 'touch': True}
        simplex = [simplex[k] for k in keep]
        lam = lam[keep]
    pa = sum(l * A[s[0]] for l, s in zip(lam, simplex))
    pb = sum(l * B[s[1]] for l, s in zip(lam, simplex))
    return {'dist': float(np.linalg.norm(v)), 'history': history, 'touch': False,
            'pa': pa, 'pb': pb}


def _closest_on_simplex(pts: np.ndarray) -> tuple[np.ndarray, list[int] | None, np.ndarray]:
    """Nearest point to the origin on a point, segment or triangle, and which corners it uses."""
    n = len(pts)
    if n == 2:
        a, b = pts
        ab = b - a
        t = float(np.clip(-np.dot(a, ab) / np.dot(ab, ab), 0, 1))
        lam = np.array([1 - t, t])
        if t <= 0:
            return a, [0], np.array([1.0, 0.0])
        if t >= 1:
            return b, [1], np.array([0.0, 1.0])
        return a + t * ab, [0, 1], lam
    # triangle: is the origin inside?
    a, b, c = pts
    def cross(u: np.ndarray, w: np.ndarray) -> float:
        return float(u[0] * w[1] - u[1] * w[0])
    s1, s2, s3 = cross(b - a, -a), cross(c - b, -b), cross(a - c, -c)
    if (s1 >= 0 and s2 >= 0 and s3 >= 0) or (s1 <= 0 and s2 <= 0 and s3 <= 0):
        return np.zeros(2), None, np.zeros(3)
    best = None
    for i, j in ((0, 1), (1, 2), (0, 2)):
        v, keep, lam = _closest_on_simplex(np.array([pts[i], pts[j]]))
        full = np.zeros(3)
        full[[i, j]] = lam
        dist = np.linalg.norm(v)
        if best is None or dist < best[0]:
            best = (dist, v, [[i, j][k] for k in keep], full)
    _, v, keep, full = best
    return v, keep, full


def convex_hull(P: np.ndarray) -> np.ndarray:
    """Andrew's monotone chain, anticlockwise."""
    P = np.unique(np.round(P, 9), axis=0)
    P = P[np.lexsort((P[:, 1], P[:, 0]))]
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower: list = []
    for p in P:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in P[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def difference_shape(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return convex_hull((A[:, None, :] - B[None, :, :]).reshape(-1, 2))


def penetration(A: np.ndarray, B: np.ndarray) -> tuple[float, np.ndarray]:
    """For overlapping shapes: the shortest move of A that separates them.

    It is the distance from the origin to the nearest edge of the difference
    shape. EPA, the expanding polytope algorithm, finds the same edge by growing
    GJK's last triangle; here the whole difference shape is small, so the script
    checks every edge.
    """
    H = difference_shape(A, B)
    best = (np.inf, None)
    for i in range(len(H)):
        a, b = H[i], H[(i + 1) % len(H)]
        e = b - a
        n = np.array([e[1], -e[0]]) / np.linalg.norm(e)      # outward for an anticlockwise hull
        d = float(np.dot(n, a))
        if d < best[0]:
            best = (d, n)
    return best[0], best[1]


def brute_distance(A: np.ndarray, B: np.ndarray) -> float:
    """Check GJK: the smallest distance between any corner and any edge of the two polygons."""
    best = np.inf
    for P, Q in ((A, B), (B, A)):
        for p in P:
            for i in range(len(Q)):
                best = min(best, _point_seg_dist(p, Q[i], Q[(i + 1) % len(Q)]))
    return float(best)


# ---- continuous checking by conservative advancement ---------------------

EDGE_A: np.ndarray = np.array([0.0, 30.0])
EDGE_B: np.ndarray = np.array([60.0, 30.0])
ROD_R: float = 0.06


def thin_rod() -> tuple[float, float, float]:
    """The same 12 cm rod as the sampling page: on the gripper's arc at joint 1 = 45 degrees."""
    _, t = _elbow_tip(np.array([45.0, 30.0]))
    return float(t[0]), float(t[1]), ROD_R


def rod_just_out_of_reach() -> tuple[float, float, float]:
    """The same rod moved 9 cm further out, so the gripper passes it with 3 cm to spare."""
    x, y, r = thin_rod()
    k = (np.hypot(x, y) + 0.09) / np.hypot(x, y)
    return float(x * k), float(y * k), r


def arm_rod_distance(q: np.ndarray, rod: tuple[float, float, float] | None = None) -> float:
    cx, cy, r = thin_rod() if rod is None else rod
    e, t = _elbow_tip(q)
    c = np.array([cx, cy])
    return min(_point_seg_dist(c, np.zeros(2), e), _point_seg_dist(c, e, t)) - r


def conservative_advancement(rod: tuple[float, float, float] | None = None, tol: float = 0.001) -> dict:
    """Move joint 1 from EDGE_A to EDGE_B in steps that are known to be safe.

    With joint 2 held still, the whole arm turns about the base. No point of it
    is further from the base than the gripper, so when joint 1 turns by a small
    angle (in radians), no point moves further than that angle times the
    gripper's distance from the base. If the arm is d metres from the rod, it can
    safely turn by d / R radians. Repeat until the arm touches or the move ends.
    """
    _, t = _elbow_tip(EDGE_A)
    R = float(np.linalg.norm(t))
    q = EDGE_A.copy()
    steps: list[tuple[float, float]] = []
    while True:
        d = arm_rod_distance(q, rod)
        steps.append((float(q[0]), d))
        if d <= tol:
            return {'steps': steps, 'contact': True, 'R': R}
        dq = np.degrees(d / R)
        if q[0] + dq >= EDGE_B[0]:
            steps.append((float(EDGE_B[0]), arm_rod_distance(EDGE_B, rod)))
            return {'steps': steps, 'contact': False, 'R': R}
        q = q + np.array([dq, 0.0])


def first_contact_angle() -> float:
    """Where the arm first touches the rod, found by fine search (for checking)."""
    qs = np.linspace(EDGE_A[0], EDGE_B[0], 6001)
    for lo, hi in zip(qs[:-1], qs[1:]):
        if arm_rod_distance(np.array([hi, 30.0])) <= 0:
            for _ in range(40):
                mid = (lo + hi) / 2
                if arm_rod_distance(np.array([mid, 30.0])) <= 0:
                    hi = mid
                else:
                    lo = mid
            return float(hi)
    return float('nan')


# ==========================================================================
# PART 2: planning with a rule on the way (keep the cup upright)
# ==========================================================================

# A three-joint arm seen from the side, holding a cup. Lengths in metres.
C_L: tuple[float, float, float] = (0.40, 0.30, 0.10)
C_LIMITS: np.ndarray = np.array([[-120.0, 180.0], [-170.0, 170.0], [-170.0, 170.0]])
C_BASE: np.ndarray = np.array([0.0, 0.40])      # the shoulder sits on a post 40 cm above the table
SHELF: tuple[float, float, float, float] = (0.32, 0.40, 0.0, 0.18)     # x0, x1, z0, z1: a box on the table
CUP_W: float = 0.07
CUP_H: float = 0.09
C_TOOL_START: np.ndarray = np.array([0.62, 0.03])
C_TOOL_GOAL: np.ndarray = np.array([0.22, 0.03])


def tilt(q: np.ndarray) -> np.ndarray:
    """How far the cup leans from upright, in degrees: the hand's angle to the horizontal."""
    t = np.asarray(q)[..., 0] + np.asarray(q)[..., 1] + np.asarray(q)[..., 2]
    return (t + 180.0) % 360.0 - 180.0


def c_joints(q: np.ndarray) -> np.ndarray:
    """Base, elbow, wrist and hand-end positions."""
    a = np.cumsum(np.radians(q))
    pts = [C_BASE.copy()]
    for L, ang in zip(C_L, a):
        pts.append(pts[-1] + L * np.array([np.cos(ang), np.sin(ang)]))
    return np.array(pts)


def cup_corners(q: np.ndarray) -> np.ndarray:
    """The cup stands on the end of the hand, and leans with it."""
    P = c_joints(q)
    ang = np.radians(np.sum(q))
    R = rot(np.degrees(ang))
    local = np.array([[-CUP_W / 2, 0], [CUP_W / 2, 0], [CUP_W / 2 + 0.01, CUP_H], [-CUP_W / 2 - 0.01, CUP_H]])
    return P[-1] + local @ R.T


def c_free(q: np.ndarray) -> bool:
    if np.any(q < C_LIMITS[:, 0]) or np.any(q > C_LIMITS[:, 1]):
        return False
    P = c_joints(q)
    pts = []
    for i in range(3):
        for t in np.linspace(0, 1, 9):
            pts.append(P[i] + t * (P[i + 1] - P[i]))
    C = cup_corners(q)
    for i in range(4):
        for t in np.linspace(0, 1, 5):
            pts.append(C[i] + t * (C[(i + 1) % 4] - C[i]))
    pts = np.array(pts)
    if np.any(pts[:, 1] < -1e-9):          # below the table top
        return False
    x0, x1, z0, z1 = SHELF
    inside = (pts[:, 0] >= x0 - 0.01) & (pts[:, 0] <= x1 + 0.01) & (pts[:, 1] <= z1 + 0.01)
    return not bool(inside.any())


def c_ik(tool: np.ndarray) -> np.ndarray:
    """Joint angles that put the hand end at `tool` with the hand level, elbow up."""
    wrist = tool - np.array([C_L[2], 0.0]) - C_BASE
    x, z = wrist
    L1c, L2c = C_L[0], C_L[1]
    c2 = (x * x + z * z - L1c ** 2 - L2c ** 2) / (2 * L1c * L2c)
    q2 = -np.arccos(np.clip(c2, -1, 1))
    q1 = np.arctan2(z, x) - np.arctan2(L2c * np.sin(q2), L1c + L2c * np.cos(q2))
    q = np.degrees(np.array([q1, q2, 0.0]))
    q[2] = -(q[0] + q[1])
    return q


def project_upright(q: np.ndarray) -> np.ndarray:
    """Pull a configuration onto the rule tilt = 0 with Newton steps.

    The rule is F(q) = q1 + q2 + q3 = 0. Its gradient is (1, 1, 1). One Newton
    step moves q by the smallest change that makes F zero: subtract F/3 from
    each joint. For this rule one step is exact; for a curved rule it takes a few.
    """
    F = float(tilt(q))
    return q - F / 3.0


def _c_edge_free(a: np.ndarray, b: np.ndarray, step: float = 2.0, rule: bool = False) -> bool:
    n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
    for t in np.linspace(0, 1, n + 1)[1:]:
        q = a + t * (b - a)
        if rule:
            q = project_upright(q)
        if not c_free(q):
            return False
    return True


def c_rrt_connect(seed: int, rule: bool, step: float = 8.0, max_iter: int = 20000) -> dict:
    """RRT-Connect for the three-joint arm, with or without the upright rule (by projection)."""
    rng = np.random.default_rng(seed)
    qs, qg = c_ik(C_TOOL_START), c_ik(C_TOOL_GOAL)
    trees = [([qs], [-1]), ([qg], [-1])]
    samples = 0

    def steer(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        d = b - a
        n = np.linalg.norm(d)
        q = b.copy() if n <= step else a + d * step / n
        return project_upright(q) if rule else q

    def extend(tree: tuple, target: np.ndarray) -> tuple[str, int]:
        nodes, parent = tree
        i = int(np.argmin([np.linalg.norm(n - target) for n in nodes]))
        new = steer(nodes[i], target)
        if c_free(new) and _c_edge_free(nodes[i], new, rule=rule):
            nodes.append(new)
            parent.append(i)
            return ('reached' if np.linalg.norm(new - target) < 1e-6 else 'advanced'), len(nodes) - 1
        return 'trapped', -1

    for it in range(max_iter):
        x = rng.uniform(C_LIMITS[:, 0], C_LIMITS[:, 1])
        samples += 1
        if rule:
            x = project_upright(x)
        a, b = trees[it % 2], trees[1 - it % 2]
        s, ia = extend(a, x)
        if s == 'trapped':
            continue
        target = a[0][ia]
        while True:
            s2, ib = extend(b, target)
            if s2 != 'advanced':
                break
        if s2 == 'reached':
            pa = _tree_path(*a, ia)
            pb = _tree_path(*b, ib)
            path = pa + pb[::-1][1:] if it % 2 == 0 else pb + pa[::-1][1:]
            return {'path': path, 'iterations': it + 1, 'samples': samples}
    return {'path': None, 'iterations': max_iter, 'samples': samples}


def _tree_path(nodes: list, parent: list, i: int) -> list:
    out = [nodes[i]]
    while parent[i] >= 0:
        i = parent[i]
        out.append(nodes[i])
    return out[::-1]


def c_shortcut(path: list, seed: int, rule: bool, tries: int = 200) -> list:
    rng = np.random.default_rng(seed)
    p = list(path)
    for _ in range(tries):
        if len(p) < 3:
            break
        i, j = sorted(rng.choice(len(p), 2, replace=False))
        if j - i < 2:
            continue
        if _c_edge_free(p[i], p[j], rule=rule):
            p = p[:i + 1] + p[j:]
    return p


def dense(path: list, step: float = 1.0) -> np.ndarray:
    out = [path[0]]
    for a, b in zip(path[:-1], path[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        for t in np.linspace(0, 1, n + 1)[1:]:
            out.append(a + t * (b - a))
    return np.array(out)


def random_tilts(n: int = 10000, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    q = rng.uniform(C_LIMITS[:, 0], C_LIMITS[:, 1], size=(n, 3))
    return tilt(q)


# ---- projection onto a curved rule, on the two-joint arm ----------------

LINE_Y: float = 2.5      # the rule: keep the gripper on the line y = 2.5 m (seen from above)


def line_rule(q: np.ndarray) -> float:
    _, t = _elbow_tip(q)
    return float(t[1] - LINE_Y)


def line_rule_grad(q: np.ndarray) -> np.ndarray:
    """d(gripper y)/d(joint angles in degrees)."""
    a = np.radians(q[0])
    b = a + np.radians(q[1])
    return np.radians(1.0) * np.array([L1 * np.cos(a) + L2 * np.cos(b), L2 * np.cos(b)])


def project_line(q: np.ndarray, tol: float = 1e-4, max_iter: int = 20) -> tuple[np.ndarray, list[np.ndarray]]:
    """Newton steps: move q by the smallest change that would make the rule hold, if it were straight."""
    steps = [q.copy()]
    for _ in range(max_iter):
        F = line_rule(q)
        if abs(F) < tol:
            break
        g = line_rule_grad(q)
        q = q - g * F / float(np.dot(g, g))
        steps.append(q.copy())
    return q, steps


def projected_samples(n: int = 6, seed: int = 2) -> list[tuple[np.ndarray, np.ndarray, list[np.ndarray]]]:
    """Random samples projected onto the rule. A projection that leaves the joint
    limits or does not settle is thrown away, as a real planner would."""
    rng = np.random.default_rng(seed)
    out = []
    tried = 0
    while len(out) < n:
        tried += 1
        q0 = rng.uniform([-180, -160], [180, 160])
        qe, st = project_line(q0)
        ok = abs(line_rule(qe)) < 1e-4 and all(-180 <= q[0] <= 180 and -160 <= q[1] <= 160 for q in st)
        if ok:
            out.append((q0, qe, st))
    projected_samples.tried = tried
    return out


def line_rule_grid(res: float = 0.5) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    q1 = np.arange(-180, 180 + res, res)
    q2 = np.arange(-160, 160 + res, res)
    Q1, Q2 = np.meshgrid(q1, q2)
    a = np.radians(Q1)
    b = a + np.radians(Q2)
    Y = L1 * np.sin(a) + L2 * np.sin(b)
    return Q1, Q2, Y - LINE_Y


# ==========================================================================
# PART 3: sampling-based optimisation and model predictive control
# ==========================================================================

# A block on a table, seen from above, in centimetres. Each action is one push:
# the pusher moves by (ux, uy), at most MAX_PUSH long.
P_START: np.ndarray = np.array([0.0, 0.0])
P_TARGET: np.ndarray = np.array([20.0, 4.0])
MUG: tuple[float, float, float] = (10.0, 2.0, 5.0)     # centre x, y, and the block's keep-out radius
MAX_PUSH: float = 5.0
MODEL: tuple[float, float] = (0.8, 0.15)      # the planner's push model: how far it slides, how far it drifts
REAL: tuple[float, float] = (0.65, 0.30)      # the real block: heavier, and pushed further off centre
HIT_PENALTY: float = 100.0


def clip_push(u: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(u, axis=-1, keepdims=True)
    return u * np.minimum(1.0, MAX_PUSH / np.maximum(n, 1e-12))


def push_step(p: np.ndarray, u: np.ndarray, params: tuple[float, float] = MODEL) -> np.ndarray:
    """One push. The block slides `slide` times as far as the pusher, and drifts to
    the left by `drift` times the push length, because the pusher meets it a little
    off centre."""
    slide, drift = params
    u = clip_push(u)
    left = np.stack([-u[..., 1], u[..., 0]], -1)
    return p + slide * u + drift * left


def _seg_hits_mug(a: np.ndarray, b: np.ndarray, margin: float = 0.0) -> np.ndarray:
    c = np.array(MUG[:2])
    ab = b - a
    denom = np.maximum((ab * ab).sum(-1), 1e-12)
    t = np.clip(((c - a) * ab).sum(-1) / denom, 0, 1)
    closest = a + t[..., None] * ab
    return np.linalg.norm(closest - c, axis=-1) < MUG[2] + margin


def rollout(p0: np.ndarray, U: np.ndarray, params: tuple[float, float] = MODEL) -> np.ndarray:
    """U has shape (..., H, 2). Returns positions, shape (..., H + 1, 2)."""
    ps = [np.broadcast_to(p0, U.shape[:-2] + (2,))]
    for k in range(U.shape[-2]):
        ps.append(push_step(ps[-1], U[..., k, :], params))
    return np.stack(ps, -2)


def score(p0: np.ndarray, U: np.ndarray, params: tuple[float, float] = MODEL) -> np.ndarray:
    """Distance from the final position to the target, plus 100 if the block touches the mug."""
    P = rollout(p0, U, params)
    hit = _seg_hits_mug(P[..., :-1, :], P[..., 1:, :]).any(-1)
    return np.linalg.norm(P[..., -1, :] - P_TARGET, axis=-1) + HIT_PENALTY * hit


MPC_MARGIN: float = 1.5     # MPC keeps 1.5 cm further from the mug, because its model is not exact


def score_mpc(p0: np.ndarray, U: np.ndarray, params: tuple[float, float] = MODEL) -> np.ndarray:
    """The score MPC uses. The average distance to the target over the pushes, so it
    gets there soon and stays there. Plus 100 if the block touches the mug. Plus 20 for
    every centimetre the block comes inside a 1.5 cm margin around the mug."""
    P = rollout(p0, U, params)
    hit = _seg_hits_mug(P[..., :-1, :], P[..., 1:, :]).any(-1)
    gap = np.linalg.norm(P[..., 1:, :] - np.array(MUG[:2]), axis=-1) - MUG[2]
    inside = np.clip(MPC_MARGIN - gap, 0, None).sum(-1)
    return (np.linalg.norm(P[..., 1:, :] - P_TARGET, axis=-1).mean(-1) + HIT_PENALTY * hit
            + 20.0 * inside)


H_PLAN: int = 8          # the one-off plan: 8 pushes, so 16 numbers to choose


def random_shooting(p0: np.ndarray, n: int, H: int, rng: np.random.Generator) -> dict:
    U = rng.uniform(-MAX_PUSH, MAX_PUSH, size=(n, H, 2))
    s = score(p0, U)
    best = int(np.argmin(s))
    return {'U': U, 'scores': s, 'best': U[best], 'best_score': float(s[best]),
            'curve': np.minimum.accumulate(s)}


def cem(p0: np.ndarray, H: int, rng: np.random.Generator, pop: int = 50, elites: int = 5,
        iters: int = 8, mean: np.ndarray | None = None, std: float = 3.0, cost=None) -> dict:
    """The cross-entropy method: sample around a mean, keep the best few, move the
    mean and the spread to fit them, and repeat."""
    mu = np.zeros((H, 2)) if mean is None else mean.copy()
    sd = np.full((H, 2), std)
    history = []
    best_U, best_s = None, np.inf
    curve = []
    for _ in range(iters):
        U = mu + sd * rng.standard_normal((pop, H, 2))
        U = clip_push(U)
        s = (score if cost is None else cost)(p0, U)
        order = np.argsort(s)
        E = U[order[:elites]]
        history.append({'U': U, 'scores': s, 'elite': order[:elites], 'mean': mu.copy(), 'std': sd.copy()})
        for v in s:
            curve.append(float(v) if not curve else min(curve[-1], float(v)))
        if s[order[0]] < best_s:
            best_s, best_U = float(s[order[0]]), U[order[0]]
        mu = E.mean(0)
        sd = E.std(0) + 0.05
    return {'best': best_U, 'best_score': best_s, 'history': history, 'mean': mu, 'curve': np.array(curve)}


def cma_es(p0: np.ndarray, H: int, rng: np.random.Generator, budget: int = 400,
           sigma0: float = 3.0) -> dict:
    """CMA-ES, the covariance matrix adaptation evolution strategy, in its standard form.

    Like CEM it keeps a cloud of guesses described by a mean and a spread. It
    also learns a full covariance matrix, which says which combinations of the
    numbers to try together, and a step size that grows when progress is steady
    and shrinks when it is not.
    """
    n = 2 * H
    lam = 4 + int(3 * np.log(n))
    mu = lam // 2
    w = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
    w /= w.sum()
    mueff = 1.0 / np.sum(w ** 2)
    cc = (4 + mueff / n) / (n + 4 + 2 * mueff / n)
    cs = (mueff + 2) / (n + mueff + 5)
    c1 = 2 / ((n + 1.3) ** 2 + mueff)
    cmu = min(1 - c1, 2 * (mueff - 2 + 1 / mueff) / ((n + 2) ** 2 + mueff))
    damps = 1 + 2 * max(0, np.sqrt((mueff - 1) / (n + 1)) - 1) + cs
    chin = np.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))
    m = np.zeros(n)
    sigma = sigma0
    C = np.eye(n)
    pc = np.zeros(n)
    ps = np.zeros(n)
    evals = 0
    best_s, best_U = np.inf, None
    curve: list[float] = []
    gen = 0
    while evals + lam <= budget:
        gen += 1
        vals, vecs = np.linalg.eigh(C)
        vals = np.maximum(vals, 1e-20)
        Bm, D = vecs, np.sqrt(vals)
        z = rng.standard_normal((lam, n))
        y = z * D @ Bm.T
        X = m + sigma * y
        U = clip_push(X.reshape(lam, H, 2))
        s = score(p0, U)
        evals += lam
        for v in s:
            best_s_new = min(best_s, float(v))
            if best_s_new < best_s:
                best_s = best_s_new
            curve.append(best_s)
        i_best = int(np.argmin(s))
        if s[i_best] <= best_s:
            best_U = U[i_best]
        order = np.argsort(s)
        ysel = y[order[:mu]]
        m_old = m
        m = m + sigma * (w @ ysel)
        Cinvsqrt = Bm @ np.diag(1 / D) @ Bm.T
        ps = (1 - cs) * ps + np.sqrt(cs * (2 - cs) * mueff) * Cinvsqrt @ ((m - m_old) / sigma)
        hsig = np.linalg.norm(ps) / np.sqrt(1 - (1 - cs) ** (2 * gen)) / chin < 1.4 + 2 / (n + 1)
        pc = (1 - cc) * pc + hsig * np.sqrt(cc * (2 - cc) * mueff) * ((m - m_old) / sigma)
        C = ((1 - c1 - cmu) * C + c1 * (np.outer(pc, pc) + (1 - hsig) * cc * (2 - cc) * C)
             + cmu * (ysel.T * w) @ ysel)
        sigma *= np.exp((cs / damps) * (np.linalg.norm(ps) / chin - 1))
    return {'best': best_U, 'best_score': best_s, 'curve': np.array(curve), 'lam': lam, 'gens': gen}


BUDGET: int = 400


def compare_methods(n_seeds: int = 20) -> dict:
    """Best score after each evaluation, for each method, over n_seeds runs."""
    out: dict = {'Random shooting': [], 'Cross-entropy method': [], 'CMA-ES': []}
    for sd in range(n_seeds):
        out['Random shooting'].append(random_shooting(P_START, BUDGET, H_PLAN, np.random.default_rng(sd))['curve'])
        out['Cross-entropy method'].append(cem(P_START, H_PLAN, np.random.default_rng(sd))['curve'])
        c = cma_es(P_START, H_PLAN, np.random.default_rng(sd), budget=BUDGET)['curve']
        out['CMA-ES'].append(np.concatenate([c, np.full(BUDGET - len(c), c[-1])]))
    return {k: np.array(v) for k, v in out.items()}


H_MPC: int = 5


def mpc(params_real: tuple[float, float], steps: int = 12, seed: int = 3) -> dict:
    """Plan 5 pushes with CEM, do only the first on the real block, look again, re-plan."""
    rng = np.random.default_rng(seed)
    p = P_START.copy()
    real = [p.copy()]
    plans = []
    mean = None
    hits = False
    for _ in range(steps):
        r = cem(p, H_MPC, rng, pop=60, elites=6, iters=6, mean=mean, cost=score_mpc)
        plans.append(rollout(p, r['best'][None])[0])
        u = r['best'][0]
        p_new = push_step(p, u, params_real)
        hits = hits or bool(_seg_hits_mug(p, p_new))
        p = p_new
        real.append(p.copy())
        mean = np.concatenate([r['mean'][1:], np.zeros((1, 2))])      # warm start: shift the plan by one
    return {'real': np.array(real), 'plans': plans, 'hits': hits}


def open_loop(seed: int = 0) -> dict:
    """Plan all 8 pushes once with CMA-ES, then do them all on the real block without looking."""
    r = cma_es(P_START, H_PLAN, np.random.default_rng(seed), budget=BUDGET)
    planned = rollout(P_START, r['best'][None])[0]
    real = rollout(P_START, r['best'][None], REAL)[0]
    hit = bool(_seg_hits_mug(real[:-1], real[1:]).any())
    return {'planned': planned, 'real': real, 'hit': hit, 'score': r['best_score']}


# ==========================================================================
# drawing: how a collision checker answers
# ==========================================================================

def _draw_scene(ax: Axes, alpha: float = 1.0) -> None:
    ax.add_patch(Rectangle((BOX[0], BOX[2]), BOX[1] - BOX[0], BOX[3] - BOX[2],
                           facecolor=OBST_COLOURS[0], edgecolor='none', alpha=0.85 * alpha, zorder=2))
    for i, (cx, cy, r) in enumerate(POSTS):
        ax.add_patch(Circle((cx, cy), r, facecolor=OBST_COLOURS[i + 1], edgecolor='none',
                            alpha=0.85 * alpha, zorder=2))


def _box_patch(b: tuple, colour: str, lw: float = 1.6, ls: str = '--', fill: str = 'none',
               alpha: float = 1.0, z: int = 3) -> Rectangle:
    return Rectangle((b[0], b[2]), b[1] - b[0], b[3] - b[2], facecolor=fill, edgecolor=colour,
                     lw=lw, ls=ls, alpha=alpha, zorder=z)


def bounding_volumes_picture() -> None:
    rects = link_rectangles(BV_Q)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.2), facecolor='white',
                             gridspec_kw={'width_ratios': [1, 1.25]})

    # left: one link, three ways to wrap it
    ax = axes[0]
    r = rects[1]
    b = aabb(r)
    _axes(ax, (b[0] - 0.55, b[1] + 0.55), (b[2] - 0.9, b[3] + 0.5))
    ax.add_patch(Polygon(r, closed=True, facecolor=LINK, edgecolor='none', alpha=0.9, zorder=4))
    ax.add_patch(_box_patch(b, GRIP, lw=2, z=5))
    cs, rr = spheres_for_rect(r, 4)
    for c in cs:
        ax.add_patch(Circle(c, rr, facecolor='none', edgecolor=SLIDE, lw=1.8, zorder=6))
    area_box = (b[1] - b[0]) * (b[3] - b[2])
    area = L2 * LINK_WIDTH
    ax.text(b[0], b[3] + 0.12, f'axis-aligned box: {area_box:.2f} m², {area_box / area:.1f} times the link',
            color=GRIP, fontsize=10.5, ha='left', va='bottom')
    ax.text(b[1] - 0.05, b[2] - 0.12, f'4 spheres of radius {rr * 100:.0f} cm', color=SLIDE,
            fontsize=10.5, ha='right', va='top')
    ax.text((b[0] + b[1]) / 2, b[2] - 0.6, f'link 2 itself: {L2:.0f} m × {LINK_WIDTH * 100:.0f} cm = {area:.2f} m²',
            color=LINK, fontsize=10.5, ha='center', va='top')
    _title(ax, 'One link, wrapped two ways')

    # right: the whole scene, and which pairs go on to the exact test
    ax = axes[1]
    _axes(ax, (-4.5, 5.9), (-1.6, 5.0))
    _draw_scene(ax)
    for rct in rects:
        ax.add_patch(Polygon(rct, closed=True, facecolor=LINK, edgecolor='none', alpha=0.9, zorder=4))
    ax.plot(0, 0, 'o', color=JOINT, ms=9, zorder=6)
    obs = obstacle_aabbs()
    over = {(i, j): (ov, gap) for i, j, ov, gap in broad_phase()}
    for j, ob in enumerate(obs):
        hit = any(over[(i, j)][0] for i in range(2))
        ax.add_patch(_box_patch(ob, INK if hit else MUTED, lw=2 if hit else 1.2, z=3))
    for i, rct in enumerate(rects):
        hit = any(over[(i, j)][0] for j in range(3))
        ax.add_patch(_box_patch(aabb(rct), INK if hit else MUTED, lw=2 if hit else 1.2, z=5))
    gap = over[(1, 1)][1]
    pb = obs[1]
    ax.annotate(f'these two boxes overlap,\nso this pair gets the exact test:\ngap {gap * 100:.0f} cm, no collision',
                (pb[0] + 0.1, pb[2] + 0.1), xytext=(4.3, -1.5), fontsize=10, color=INK, ha='center', va='bottom',
                arrowprops=dict(arrowstyle='->', color=INK, lw=1))
    ax.text(-4.4, -1.5, '2 links × 3 objects = 6 pairs\n5 pairs ruled out by boxes alone',
            fontsize=10.5, color=INK, ha='left', va='bottom')
    for j, name in enumerate(OBST_NAMES):
        ob = obs[j]
        ax.text((ob[0] + ob[1]) / 2, ob[3] + 0.08, name, fontsize=10, color=OBST_COLOURS[j],
                ha='center', va='bottom', weight='bold')
    _title(ax, 'Cheap box test first: only overlapping pairs go further')
    fig.tight_layout(w_pad=2)
    _save(fig, SBP, 'bounding-volumes.svg')


def bounding_volume_tree_picture() -> None:
    segs = mug_segments()
    root = BVNode(np.arange(len(segs)), segs, 0)
    nodes = _all_nodes(root)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.6), facecolor='white')
    lims = ((-5.2, 8.2), (-5.4, 7.2))
    level_colours = {1: GRIP, 2: WRIST, 3: PURPLE}
    level_widths = {1: 3.6, 2: 2.2, 3: 1.2}

    def mug(ax: Axes, colour: str = INK, alpha: float = 1.0) -> None:
        for s in segs:
            ax.plot(s[:, 0], s[:, 1], color=colour, lw=1.6, alpha=alpha, zorder=4, solid_capstyle='round')

    ax = axes[0]
    _axes(ax, *lims)
    mug(ax)
    for n in nodes:
        if n.depth in level_colours:
            ax.add_patch(_box_patch(n.box, level_colours[n.depth], lw=level_widths[n.depth], ls='-'))
    for d, c in level_colours.items():
        cnt = sum(1 for n in nodes if n.depth == d)
        ax.text(-5.0 + 4.3 * (d - 1), 6.9, f'level {d}: {cnt} boxes', color=c, fontsize=10.5, va='top',
                weight='bold')
    ax.text(1.5, -5.3, f'{len(segs)} edges, {len(nodes)} boxes, {sum(1 for n in nodes if not n.kids)} at the bottom',
            color=INK, fontsize=10.5, ha='center', va='top')
    _title(ax, 'A tree of boxes around a mug')

    for ax, pos, title in ((axes[1], np.array(FINGER[:2]), 'Fingertip near the mug'),
                           (axes[2], np.array([4.7, -2.2]), 'Fingertip touching the handle')):
        _axes(ax, *lims)
        q = bv_query(root, segs, pos, FINGER[2])
        mug(ax, MUTED, 0.6)
        opened = [n for n in q['visited'] if _box_circle_gap(n.box, pos) <= FINGER[2]]
        closed = [n for n in q['visited'] if _box_circle_gap(n.box, pos) > FINGER[2]]
        for n in closed:
            ax.add_patch(_box_patch(n.box, GRIP, lw=1.4, ls='--', fill='none'))
        for n in opened:
            ax.add_patch(_box_patch(n.box, SLIDE, lw=2.0, ls='-', fill='none'))
        for i in q['tested']:
            ax.plot(segs[i, :, 0], segs[i, :, 1], color=LINK, lw=4, zorder=6, solid_capstyle='round')
        ax.add_patch(Circle(pos, FINGER[2], facecolor=JOINT, edgecolor=INK, lw=1, zorder=7))
        verdict = 'touching' if q['hit'] else 'clear'
        ax.text(1.5, -5.3, f'{len(q["visited"])} boxes looked at, {len(q["tested"])} edges tested: {verdict}',
                color=INK, fontsize=10.5, ha='center', va='top')
        _title(ax, title)
    axes[1].text(-5.1, 7.1, 'green: box touched, opened\nred dashed: box missed, skipped\nblue: edge tested exactly',
                 fontsize=10, color=INK, va='top')
    fig.tight_layout(w_pad=1.5)
    _save(fig, SBP, 'bounding-volume-tree.svg')


def distance_and_penetration_picture() -> None:
    A = FINGER_SHAPE + FINGER_APART
    B = JAR_SHAPE + JAR_AT
    g = gjk(A, B)
    D = difference_shape(A, B)
    A2 = FINGER_SHAPE + FINGER_OVERLAP
    depth, n = penetration(A2, B)
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.6), facecolor='white')

    ax = axes[0]
    _axes(ax, (-6.5, 9.0), (-5.5, 5.5))
    ax.add_patch(Polygon(A, closed=True, facecolor=LINK, alpha=0.85, edgecolor='none'))
    ax.add_patch(Polygon(B, closed=True, facecolor=SLIDE, alpha=0.85, edgecolor='none'))
    ax.plot([g['pa'][0], g['pb'][0]], [g['pa'][1], g['pb'][1]], color=INK, lw=2, zorder=6)
    ax.plot(*g['pa'], 'o', color=INK, ms=5, zorder=7)
    ax.plot(*g['pb'], 'o', color=INK, ms=5, zorder=7)
    ax.annotate(f'{g["dist"]:.2f} cm apart', (g['pa'] + g['pb']) / 2, xytext=(0.2, -4.6), fontsize=10.5,
                color=INK, ha='center', arrowprops=dict(arrowstyle='->', color=INK, lw=1))
    ax.text(FINGER_APART[0] - 0.8, 4.4, 'finger', color=LINK, fontsize=11, ha='center', weight='bold')
    ax.text(JAR_AT[0], 4.4, 'jar', color=SLIDE, fontsize=11, ha='center', weight='bold')
    _title(ax, 'Two shapes and the gap between them')

    ax = axes[1]
    _axes(ax, (D[:, 0].min() - 0.8, 2.6), (D[:, 1].min() - 3.2, D[:, 1].max() + 2.4))
    ax.add_patch(Polygon(D, closed=True, facecolor=PURPLE, alpha=0.25, edgecolor=PURPLE, lw=1.5))
    pts = (A[:, None, :] - B[None, :, :]).reshape(-1, 2)
    ax.plot(pts[:, 0], pts[:, 1], '.', color=PURPLE, ms=5)
    ax.plot(0, 0, '+', color=INK, ms=14, mew=2, zorder=7)
    ax.text(0.0, 0.7, 'origin', fontsize=10, color=INK, ha='center')
    v = g['history'][-1]['v']
    ax.plot([0, v[0]], [0, v[1]], color=INK, lw=2, zorder=6)
    ax.plot(*v, 'o', color=INK, ms=5, zorder=7)
    simp = np.array([A[i] - B[j] for i, j in g['history'][-1]['simplex']])
    if len(simp) == 2:
        ax.plot(simp[:, 0], simp[:, 1], color=GRIP, lw=3, zorder=5)
    ax.annotate(f'nearest point to the origin\n{np.linalg.norm(v):.2f} cm away: the same gap',
                v, xytext=(-4.0, D[:, 1].min() - 3.0), fontsize=10.5, color=INK, ha='center', va='bottom',
                arrowprops=dict(arrowstyle='->', color=INK, lw=1))
    ax.text(D[:, 0].min() - 0.7, D[:, 1].max() + 2.3, f'finger minus jar: {len(pts)} corner differences,\n'
            f'{len(D)} of them on the outline; red: GJK\'s last edge', fontsize=10.5, color=PURPLE, va='top')
    _title(ax, 'The difference shape that GJK searches')

    ax = axes[2]
    _axes(ax, (-5.0, 9.5), (-5.5, 5.5))
    ax.add_patch(Polygon(B, closed=True, facecolor=SLIDE, alpha=0.85, edgecolor='none'))
    ax.add_patch(Polygon(A2, closed=True, facecolor=LINK, alpha=0.75, edgecolor='none'))
    ax.add_patch(Polygon(A2 - depth * n, closed=True, facecolor='none', edgecolor=LINK, lw=1.5, ls='--'))
    c = A2.mean(0)
    ax.annotate('', c - depth * n, xytext=c, arrowprops=dict(arrowstyle='->', color=INK, lw=2))
    ax.text(-4.8, -4.4, f'overlap: the shortest move that\nseparates them is {depth:.2f} cm',
            fontsize=10.5, color=INK, va='top')
    ax.text(c[0] - depth * n[0] - 1.2, 4.3, 'moved out', color=LINK, fontsize=10, ha='center')
    _title(ax, 'Penetration depth when they overlap')
    fig.tight_layout(w_pad=1.5)
    _save(fig, SBP, 'distance-and-penetration.svg')


def _draw_arm2(ax: Axes, q: np.ndarray, colour: str, alpha: float = 1.0, lw: float = 2.5) -> None:
    e, t = _elbow_tip(q)
    ax.plot([0, e[0], t[0]], [0, e[1], t[1]], color=colour, lw=lw, alpha=alpha,
            solid_capstyle='round', zorder=4)


def continuous_checking_picture() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), facecolor='white')
    cases = ((axes[0], None, 'Rod on the path: contact found'),
             (axes[1], rod_just_out_of_reach(), 'Rod 3 cm out of reach: move proven clear'))
    for ax, rod, title in cases:
        _axes(ax, (-0.8, 5.6), (-0.8, 5.6))
        ca = conservative_advancement(rod)
        for q in EDGE_A + np.linspace(0, 1, 61)[:, None] * (EDGE_B - EDGE_A):
            _draw_arm2(ax, q, LINK_PALE, alpha=0.5, lw=2)
        for k, (a, d) in enumerate(ca['steps']):
            last = k == len(ca['steps']) - 1
            col = GRIP if (last and ca['contact']) else LINK
            _draw_arm2(ax, np.array([a, 30.0]), col, lw=2.8)
        rr = thin_rod() if rod is None else rod
        ax.add_patch(Circle(rr[:2], rr[2] * 2.2, facecolor=INK, edgecolor='none', zorder=8))
        ax.plot(0, 0, 'o', color=JOINT, ms=9, zorder=9)
        n = len(ca['steps'])
        angles = ', '.join(f'{a:.1f}' for a, _ in ca['steps']) if n <= 4 else \
            ', '.join(f'{a:.1f}' for a, _ in ca['steps'][:3]) + ', … , ' + f'{ca["steps"][-1][0]:.1f}'
        verdict = (f'{n} distance queries; touches at joint 1 = {ca["steps"][-1][0]:.2f}°'
                   if ca['contact'] else f'{n} distance queries; nearest gap {min(d for _, d in ca["steps"]) * 100:.0f} cm')
        ax.text(2.4, -0.75, verdict + f'\nposes checked (joint 1, degrees): {angles}',
                fontsize=10, color=INK, ha='center', va='top')
        _title(ax, title)
    axes[0].text(-0.7, 5.5, 'dark blue: the poses checked; each step turns\njoint 1 by (gap ÷ 4.84 m) radians, a turn no\n'
                 'point of the arm can use to reach the rod', fontsize=10, color=INK, va='top')
    axes[1].text(-0.7, 5.5, 'the rod is drawn larger than it is', fontsize=10, color=INK, va='top')
    fig.tight_layout(w_pad=2)
    _save(fig, SBP, 'continuous-checking.svg')


# ==========================================================================
# drawing: planning with a rule on the way
# ==========================================================================

def _draw_c_arm(ax: Axes, q: np.ndarray, colour: str, alpha: float = 1.0, lw: float = 3.0,
                cup_colour: str | None = None) -> None:
    P = c_joints(q)
    ax.plot(P[:, 0], P[:, 1], color=colour, lw=lw, alpha=alpha, solid_capstyle='round', zorder=4)
    C = cup_corners(q)
    ax.add_patch(Polygon(C, closed=True, facecolor=cup_colour or colour, edgecolor='none',
                         alpha=alpha, zorder=5))


def _draw_c_cup(ax: Axes, q: np.ndarray, colour: str) -> None:
    ax.add_patch(Polygon(cup_corners(q), closed=True, facecolor=colour, edgecolor='white', lw=0.8, zorder=6))


def _draw_c_scene(ax: Axes) -> None:
    ax.add_patch(Rectangle((-0.2, -0.04), 1.05, 0.04, facecolor=TABLE, edgecolor='none', zorder=1))
    ax.add_patch(Rectangle((-0.03, 0.0), 0.06, C_BASE[1], facecolor=MUTED, edgecolor='none', zorder=2))
    x0, x1, z0, z1 = SHELF
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, facecolor=OBST_COLOURS[0], edgecolor='none',
                           alpha=0.85, zorder=2))
    ax.plot(*C_BASE, 'o', color=JOINT, ms=9, zorder=6)


def cup_upright_picture() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8), facecolor='white')
    for ax, rule, title in ((axes[0], False, 'No rule: the cup tips over on the way'),
                            (axes[1], True, 'Rule "cup upright": every pose projected')):
        _axes(ax, (-0.25, 0.85), (-0.14, 0.95))
        _draw_c_scene(ax)
        r = c_rrt_connect(seed=0, rule=rule)
        s = c_shortcut(r['path'], seed=1, rule=rule)
        dd = dense(s, 1.0)
        if rule:
            dd = np.array([project_upright(x) for x in dd])
        tl = tilt(dd)
        idx = np.linspace(0, len(dd) - 1, 9).round().astype(int)
        for k, i in enumerate(idx):
            t = abs(tl[i])
            col = SLIDE if t <= 5 else (WRIST if t <= 45 else GRIP)
            _draw_c_arm(ax, dd[i], LINK, alpha=0.35 + 0.65 * (k in (0, len(idx) - 1)), lw=2.2,
                        cup_colour=col)
            _draw_c_cup(ax, dd[i], col)
        tip = np.array([c_joints(x)[-1] for x in dd])
        ax.plot(tip[:, 0], tip[:, 1], color=INK, lw=1.2, ls=':', zorder=3)
        _title(ax, f'{title}\nlargest cup tilt on the path: {np.abs(tl).max():.0f}°')
    axes[0].text(-0.22, -0.07, 'cup colour: green within 5° of upright, orange up to 45°, red beyond 45°',
                 fontsize=10, color=INK, ha='left', va='top')
    fig.tight_layout(w_pad=2)
    _save(fig, SBP, 'cup-upright-two-paths.svg')


def tilt_histogram_picture() -> None:
    t = random_tilts()
    fig, ax = plt.subplots(figsize=(10, 4.4), facecolor='white')
    bins = np.arange(-180, 181, 2)
    ax.hist(t, bins=bins, color=LINK_PALE, edgecolor='white', lw=0.3)
    inb = np.abs(t) <= 2
    ax.hist(t[inb], bins=bins, color=SLIDE)
    _plain_axes(ax)
    ax.set_xlim(-180, 180)
    ax.set_xticks(range(-180, 181, 45))
    ax.set_xlabel('cup tilt of a random set of joint angles (degrees)', fontsize=11, color=INK)
    ax.set_ylabel('number of samples', fontsize=11, color=INK)
    ax.annotate(f'within ±2° of upright:\n{int(inb.sum())} of {len(t):,} samples',
                (0, 60), xytext=(70, 70), fontsize=11, color=SLIDE, ha='center',
                arrowprops=dict(arrowstyle='->', color=SLIDE, lw=1.2))
    ax.set_title('Random samples almost never satisfy the rule', fontsize=12, color=INK, weight='bold')
    fig.tight_layout()
    _save(fig, SBP, 'tilt-of-random-samples.svg')


def projection_picture() -> None:
    Q1, Q2, F = line_rule_grid(0.5)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.1, 1]})
    ax = axes[0]
    ax.contour(Q1, Q2, F, levels=[0], colors=[SLIDE], linewidths=2.5)
    _plain_axes(ax)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-160, 160)
    ax.set_xticks(range(-180, 181, 90))
    ax.set_yticks(range(-160, 161, 80))
    ax.set_xlabel('joint 1 (degrees)', fontsize=11, color=INK)
    ax.set_ylabel('joint 2 (degrees)', fontsize=11, color=INK)
    shown = []
    for q0, qe, st in projected_samples():
        st = np.array(st)
        shown.append((q0, qe, len(st) - 1))
        ax.plot(st[:, 0], st[:, 1], '-', color=INK, lw=1, zorder=4)
        ax.plot(st[1:-1, 0], st[1:-1, 1], '.', color=MUTED, ms=6, zorder=5)
        ax.plot(*q0, 'o', color=GRIP, ms=7, zorder=6)
        ax.plot(*qe, 'o', color=SLIDE, ms=7, zorder=6)
    ax.set_title('In joint space: random samples pulled onto the rule', fontsize=12, color=INK, weight='bold')
    ax.text(-175, 150, 'green line: every pose with the gripper on the rail\n'
            'red: random sample   green dot: after projection', fontsize=9.5, color=INK, va='top',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.85))

    ax = axes[1]
    _axes(ax, (-5.4, 5.4), (-2.2, 5.6))
    ax.plot([-5.3, 5.3], [LINE_Y, LINE_Y], color=SLIDE, lw=2.5, zorder=2)
    ax.text(-5.3, LINE_Y + 0.15, f'the rule: gripper on the rail at y = {LINE_Y} m', color=SLIDE, fontsize=10.5)
    q0, qe, n = min([t for t in shown if abs(t[0][1]) < 90], key=lambda t: np.linalg.norm(t[1] - t[0]))
    for q, col in ((q0, GRIP), (qe, LINK)):
        _draw_arm2(ax, q, col, lw=4)
        _, t = _elbow_tip(q)
        ax.plot(*t, 'o', color=INK, ms=5, zorder=6)
    _, t0 = _elbow_tip(q0)
    _, te = _elbow_tip(qe)
    ax.annotate('', te, xytext=t0, arrowprops=dict(arrowstyle='->', color=INK, lw=1.2))
    ax.plot(0, 0, 'o', color=JOINT, ms=9, zorder=7)
    ax.text(0, -1.9, f'sample ({q0[0]:.0f}°, {q0[1]:.0f}°), gripper at y = {t0[1]:.2f} m\n'
            f'after {n} Newton steps ({qe[0]:.1f}°, {qe[1]:.1f}°), gripper at y = {te[1]:.4f} m',
            fontsize=10, color=INK, ha='center', va='bottom')
    ax.set_title('The same projection, seen from above', fontsize=12, color=INK, weight='bold')
    fig.tight_layout(w_pad=2)
    _save(fig, SBP, 'projecting-onto-the-rule.svg')


# ==========================================================================
# drawing: sampling-based optimisation and MPC
# ==========================================================================

def _push_scene(ax: Axes, xlim: tuple = (-4, 26), ylim: tuple = (-14, 16)) -> None:
    _axes(ax, xlim, ylim)
    ax.add_patch(Circle(MUG[:2], MUG[2] - 1.5, facecolor=MUTED, edgecolor='none', zorder=2))
    ax.add_patch(Circle(MUG[:2], MUG[2], facecolor='none', edgecolor=MUTED, lw=1, ls='--', zorder=2))
    ax.add_patch(Rectangle(P_START - 1.5, 3, 3, facecolor=WRIST, edgecolor='none', zorder=6))
    ax.plot(*P_TARGET, marker='x', color=INK, ms=12, mew=2.5, zorder=7)
    ax.text(P_TARGET[0], P_TARGET[1] + 1.4, 'target', fontsize=10, color=INK, ha='center')
    ax.text(P_START[0], P_START[1] - 2.6, 'block', fontsize=10, color=WRIST, ha='center', va='top')
    ax.text(MUG[0], MUG[1], 'mug', fontsize=10, color='white', ha='center', va='center', zorder=3)


def random_shooting_picture() -> None:
    rs = random_shooting(P_START, BUDGET, H_PLAN, np.random.default_rng(0))
    P = rollout(P_START, rs['U'])
    fig, ax = plt.subplots(figsize=(8.5, 7.2), facecolor='white')
    _push_scene(ax, (-24, 30), (-19, 22))
    hit = rs['scores'] >= HIT_PENALTY
    for k in range(len(P)):
        ax.plot(P[k, :, 0], P[k, :, 1], color=GRIP if hit[k] else LINK_PALE, lw=0.7,
                alpha=0.6 if hit[k] else 0.8, zorder=1)
    best = rollout(P_START, rs['best'][None])[0]
    ax.plot(best[:, 0], best[:, 1], '-o', color=SLIDE, lw=2.5, ms=4, zorder=8)
    ax.text(-23, 21.5, f'{BUDGET} random plans of {H_PLAN} pushes, run through the push model\n'
            f'red: {int(hit.sum())} touch the mug\n'
            f'green: the best one ends {rs["best_score"]:.1f} cm from the target',
            fontsize=10.5, color=INK, va='top')
    _title(ax, 'Random shooting: try many plans, keep the best')
    fig.tight_layout()
    _save(fig, SOM, 'random-shooting.svg')


def cem_picture() -> None:
    c = cem(P_START, H_PLAN, np.random.default_rng(0))
    shown = (0, 3, 7)
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.6), facecolor='white')
    for ax, i in zip(axes, shown):
        h = c['history'][i]
        _push_scene(ax, (-8, 28), (-16, 16))
        P = rollout(P_START, h['U'])
        for k in range(len(P)):
            ax.plot(P[k, :, 0], P[k, :, 1], color=LINK_PALE, lw=0.8, zorder=1)
        for k in h['elite']:
            ax.plot(P[k, :, 0], P[k, :, 1], color=SLIDE, lw=1.8, zorder=4)
        ax.text(-7.5, -15.5, f'best {h["scores"].min():.1f} cm from target\n'
                f'typical spread per number {h["std"].mean():.2f} cm',
                fontsize=10.5, color=INK, va='bottom')
        _title(ax, f'Round {i + 1}: 50 plans, best 5 in green')
    fig.tight_layout(w_pad=1.5)
    _save(fig, SOM, 'cem-narrowing.svg')


def method_comparison_picture() -> None:
    comp = compare_methods()
    cols = {'Random shooting': MUTED, 'Cross-entropy method': LINK, 'CMA-ES': SLIDE}
    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor='white')
    x = np.arange(1, BUDGET + 1)
    for k, v in comp.items():
        med = np.median(v, 0)
        lo, hi = np.percentile(v, 25, 0), np.percentile(v, 75, 0)
        ax.fill_between(x, lo, hi, color=cols[k], alpha=0.15, lw=0)
        ax.plot(x, med, color=cols[k], lw=2.5)
        ax.text(BUDGET + 6, med[-1], f'{k}: {med[-1]:.1f} cm', color=cols[k], fontsize=10.5,
                va='center', weight='bold')
    _plain_axes(ax)
    ax.set_yscale('log')
    ax.set_ylim(0.1, 150)
    ax.set_yticks([0.1, 1, 10, 100])
    ax.set_yticklabels(['0.1', '1', '10', '100'])
    ax.set_xlim(0, BUDGET)
    ax.set_xlabel('plans scored so far', fontsize=11, color=INK)
    ax.set_ylabel('best plan so far:\ncm from target (log scale)', fontsize=11, color=INK)
    ax.set_title('Same budget, same model: median of 20 runs, band = middle half',
                 fontsize=12, color=INK, weight='bold')
    fig.tight_layout()
    _save(fig, SOM, 'best-score-per-plan.svg')


def mpc_picture() -> None:
    ol = open_loop()
    m = mpc(REAL)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.0), facecolor='white')
    ax = axes[0]
    _push_scene(ax, (-4, 26), (-9, 12))
    ax.plot(ol['planned'][:, 0], ol['planned'][:, 1], '--o', color=MUTED, lw=1.8, ms=4, zorder=5)
    ax.plot(ol['real'][:, 0], ol['real'][:, 1], '-o', color=GRIP, lw=2.5, ms=4, zorder=6)
    miss = np.linalg.norm(ol['real'][-1] - P_TARGET)
    ax.text(-3.5, -8.5, f'grey dashed: what the model predicted (ends {np.linalg.norm(ol["planned"][-1] - P_TARGET):.1f} cm away)\n'
            f'red: what the real block did (ends {miss:.1f} cm away)', fontsize=10.5, color=INK, va='bottom')
    _title(ax, 'Plan once, do all 8 pushes without looking')

    ax = axes[1]
    _push_scene(ax, (-4, 26), (-9, 12))
    for k, pl in enumerate(m['plans']):
        ax.plot(pl[:, 0], pl[:, 1], '-', color=LINK_PALE, lw=1.2, zorder=3)
        ax.plot(pl[1, 0], pl[1, 1], '.', color=LINK, ms=5, zorder=4)
    R = m['real']
    ax.plot(R[:, 0], R[:, 1], '-o', color=SLIDE, lw=2.5, ms=4, zorder=6)
    d = np.linalg.norm(R - P_TARGET, axis=1)
    first_in = int(np.argmax(d <= 1.0))
    ax.text(-3.5, -8.5, f'pale blue: the 5-push plan made before each real push\n'
            f'green: the real block, within 1 cm after {first_in} pushes, {d[-1]:.1f} cm after {len(R) - 1}',
            fontsize=10.5, color=INK, va='bottom')
    _title(ax, 'MPC: plan 5, do 1, look, plan again')
    fig.tight_layout(w_pad=2)
    _save(fig, SOM, 'mpc-versus-open-loop.svg')


# ==========================================================================
# printing the numbers
# ==========================================================================

def print_numbers() -> None:
    np.set_printoptions(precision=3, suppress=True)
    print('--- bounding volumes')
    rects = link_rectangles(BV_Q)
    for i, r in enumerate(rects):
        b = aabb(r)
        area_box = (b[1] - b[0]) * (b[3] - b[2])
        area = (L1 if i == 0 else L2) * LINK_WIDTH
        c, rr = spheres_for_rect(r, 5 if i == 0 else 4)
        print(f'link {i + 1}: area {area:.2f}  aabb {b}  aabb area {area_box:.2f}  ratio {area_box / area:.2f}'
              f'  spheres r {rr:.3f} total area {len(c) * np.pi * rr * rr:.2f}')
    for i, j, ov, gap in broad_phase():
        print(f'  link {i + 1} vs {OBST_NAMES[j]}: boxes overlap {ov} exact gap {gap}')
    segs = mug_segments()
    root = BVNode(np.arange(len(segs)), segs, 0)
    nodes = _all_nodes(root)
    print('mug segments', len(segs), 'tree nodes', len(nodes), 'depth', max(n.depth for n in nodes),
          'leaves', sum(1 for n in nodes if not n.kids))
    q = bv_query(root, segs, np.array(FINGER[:2]), FINGER[2])
    print('finger query: boxes visited', len(q['visited']), 'segments tested', len(q['tested']), 'hit', q['hit'])
    brute = min(_point_seg_dist(np.array(FINGER[:2]), s[0], s[1]) for s in segs) - FINGER[2]
    print('  brute-force gap from finger to mug', round(brute, 3))
    for pos, tag in ((np.array([4.7, -2.2]), 'touching'),):
        qq = bv_query(root, segs, pos, FINGER[2])
        print('  query at', pos, tag, 'visited', len(qq['visited']), 'tested', len(qq['tested']), 'hit', qq['hit'])
    print('--- GJK')
    A = FINGER_SHAPE + FINGER_APART
    B = JAR_SHAPE + JAR_AT
    g = gjk(A, B)
    print('apart: gjk dist', round(g['dist'], 4), 'brute', round(brute_distance(A, B), 4),
          'iterations', len(g['history']), 'pa', g['pa'], 'pb', g['pb'])
    for h in g['history']:
        print('   simplex size', len(h['simplex']), 'v', h['v'], '|v|', round(float(np.linalg.norm(h['v'])), 3))
    print('difference shape corners', len(difference_shape(A, B)), 'from', len(A) * len(B), 'differences')
    A2 = FINGER_SHAPE + FINGER_OVERLAP
    g2 = gjk(A2, B)
    d, n = penetration(A2, B)
    print('overlap: gjk touch', g2['touch'], 'iterations', len(g2['history']), 'depth', round(d, 4), 'dir', n)
    print('   after moving A by -(d+1e-6) n: gjk dist', round(gjk(A2 - (d + 1e-3) * n, B)['dist'], 4))
    print('--- continuous checking')
    ca = conservative_advancement()
    print('R', round(ca['R'], 3), 'steps', len(ca['steps']) - 1, 'contact', ca['contact'])
    for a, d in ca['steps']:
        print(f'   q1 {a:.3f}  gap {d:.4f}')
    print('first contact by fine search', round(first_contact_angle(), 3))
    ca2 = conservative_advancement(rod_just_out_of_reach())
    print('rod out of reach: queries', len(ca2['steps']), 'contact', ca2['contact'],
          'smallest gap', round(min(d for _, d in ca2['steps']), 4),
          'smallest step', round(min(np.diff([a for a, _ in ca2['steps']])), 3))
    print('--- constrained planning')
    qs, qg = c_ik(C_TOOL_START), c_ik(C_TOOL_GOAL)
    print('start', qs, 'goal', qg, 'free', c_free(qs), c_free(qg), 'tilts', tilt(qs), tilt(qg))
    print('straight joint move free?', _c_edge_free(qs, qg))
    for rule in (False, True):
        r = c_rrt_connect(seed=0, rule=rule)
        p = r['path']
        s = c_shortcut(p, seed=1, rule=rule)
        dd = dense(s)
        if rule:
            dd = np.array([project_upright(x) for x in dd])
        print(f'rule {rule}: iterations {r["iterations"]} raw waypoints {len(p)} after shortcut {len(s)}'
              f' max |tilt| raw {np.abs(tilt(dense(p))).max():.1f} after shortcut {np.abs(tilt(dd)).max():.1f}')
    t = random_tilts()
    for tol in (2.0, 5.0):
        print(f'random samples within +-{tol}: {int((np.abs(t) <= tol).sum())} of {len(t)}')
    stats = {False: [], True: []}
    for sd in range(20):
        for rule in (False, True):
            r = c_rrt_connect(seed=sd, rule=rule)
            p = r['path']
            stats[rule].append((r['iterations'], np.abs(tilt(dense(p))).max() if p is not None else np.nan))
    for rule in (False, True):
        a = np.array(stats[rule])
        print(f'rule {rule} 20 seeds: iterations median {np.median(a[:, 0])} max tilt median {np.nanmedian(a[:, 1]):.1f}'
              f' min {np.nanmin(a[:, 1]):.1f} max {np.nanmax(a[:, 1]):.1f}')
    print('--- projection onto the line rule')
    for q0, qe, st in projected_samples():
        print('  from', q0, 'to', qe, 'newton steps', len(st) - 1, 'rule error', round(line_rule(qe), 6))
    print('  samples tried', projected_samples.tried)
    Q1, Q2, F = line_rule_grid(0.5)
    print('grid cells within 1 cm of the line', round(float((np.abs(F) <= 0.01).mean() * 100), 3), '%')
    print('--- sampling optimisation')
    print('straight push line hits mug?', bool(_seg_hits_mug(P_START, P_TARGET)))
    rs = random_shooting(P_START, BUDGET, H_PLAN, np.random.default_rng(0))
    print('random shooting seed 0 best', round(rs['best_score'], 2), 'n with a hit', int((rs['scores'] >= HIT_PENALTY).sum()))
    c = cem(P_START, H_PLAN, np.random.default_rng(0))
    for i, h in enumerate(c['history']):
        print(f'  CEM iter {i + 1}: best {h["scores"].min():.2f} median {np.median(h["scores"]):.2f}'
              f' elite worst {np.sort(h["scores"])[4]:.2f} mean std {h["std"].mean():.2f}')
    print('CEM best', round(c['best_score'], 2))
    cm = cma_es(P_START, H_PLAN, np.random.default_rng(0), budget=BUDGET)
    print('CMA-ES lambda', cm['lam'], 'generations', cm['gens'], 'best', round(cm['best_score'], 2))
    comp = compare_methods()
    for k, v in comp.items():
        f = v[:, -1]
        print(f'{k}: after 100 median {np.median(v[:, 99]):.2f}; after {BUDGET} median {np.median(f):.2f}'
              f' best {f.min():.2f} worst {f.max():.2f}')
    ol = open_loop()
    print('open loop: planned final', ol['planned'][-1], 'dist', round(float(np.linalg.norm(ol['planned'][-1] - P_TARGET)), 2),
          'real final', ol['real'][-1], 'dist', round(float(np.linalg.norm(ol['real'][-1] - P_TARGET)), 2), 'hit', ol['hit'])
    m = mpc(REAL)
    d = np.linalg.norm(m['real'] - P_TARGET, axis=1)
    print('MPC real distances per step', np.round(d, 2), 'hit', m['hits'])
    m2 = mpc(MODEL)
    print('MPC on model block distances', np.round(np.linalg.norm(m2['real'] - P_TARGET, axis=1), 2))


def main() -> None:
    global PNG_DIR
    if len(sys.argv) == 2 and sys.argv[1] == '--numbers':
        print_numbers()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    bounding_volumes_picture()
    bounding_volume_tree_picture()
    distance_and_penetration_picture()
    continuous_checking_picture()
    cup_upright_picture()
    tilt_histogram_picture()
    projection_picture()
    random_shooting_picture()
    cem_picture()
    method_comparison_picture()
    mpc_picture()


if __name__ == '__main__':
    main()
