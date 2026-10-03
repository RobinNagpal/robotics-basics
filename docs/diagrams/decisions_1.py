"""Generate the diagrams for the first half of docs/06_programming-techniques/08_decisions-and-task-logic/.

This covers 01_overview, 02_finite-state-machines and 03_behaviour-trees. Each
document's pictures go to a folder named after it, under
docs/images/decisions-and-task-logic/.

Run with:  pixi run python ../docs/diagrams/decisions_1.py
Add --png <dir> to also write PNG copies for checking.
Add --trace to print the runs that the documents quote.

Every picture that shows a run is drawn from a real run. The script holds a small
state machine and a small behaviour tree engine, runs the pick-and-place task on
them with a scripted failed grasp, and draws what they did. The greedy view choice
and the mug-to-slot assignment on the overview picture are also computed here.
"""

import itertools
import math
import pathlib
import sys
from dataclasses import dataclass, field

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (Circle, Ellipse, FancyBboxPatch, Polygon,  # noqa: E402
                                Rectangle)
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

# The three answers a behaviour tree node can give, and their colours.
SUCCESS: str = 'SUCCESS'
FAILURE: str = 'FAILURE'
RUNNING: str = 'RUNNING'
STATUS_COLOUR: dict[str, str] = {SUCCESS: SLIDE, FAILURE: GRIP, RUNNING: JOINT}


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
           ha: str = 'center', weight: str = 'normal', va: str = 'center',
           box: bool = False) -> None:
    kw: dict = {}
    if box:
        kw['bbox'] = {'boxstyle': 'round,pad=0.15', 'facecolor': 'white',
                      'edgecolor': 'none'}
    ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, weight=weight,
            zorder=9, **kw)


def _title(ax: Axes, x: float, y: float, text: str, size: float = 12) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='center', color=INK, weight='bold')


def _caption(ax: Axes, x: float, y: float, text: str, size: float = 10) -> None:
    ax.text(x, y, text, fontsize=size, ha='center', va='top', color=MUTED)


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float], color: str = MUTED,
           lw: float = 1.6, style: str = '-|>', rad: float = 0.0, z: int = 5,
           ls: str = '-') -> None:
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': style, 'color': color, 'lw': lw,
                            'shrinkA': 0, 'shrinkB': 0, 'linestyle': ls,
                            'connectionstyle': f'arc3,rad={rad}'},
                zorder=z)


def _save(fig: Figure, folder: str, name: str) -> None:
    out: pathlib.Path = IMAGES / folder
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{folder}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _state_box(ax: Axes, x: float, y: float, text: str, color: str = LINK,
               w: float = 1.9, h: float = 0.7, size: float = 10, fill: str = 'white',
               lw: float = 2.0) -> None:
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle='round,pad=0.02,rounding_size=0.25',
                                facecolor=fill, edgecolor=color, lw=lw, zorder=6))
    _label(ax, x, y, text, size=size, color=INK)


def _edge_point(x0: float, y0: float, x1: float, y1: float, w: float,
                h: float) -> tuple[float, float]:
    """Where the line from box centre (x0, y0) towards (x1, y1) leaves a w by h box."""
    dx, dy = x1 - x0, y1 - y0
    if dx == 0 and dy == 0:
        return x0, y0
    tx = (w / 2) / abs(dx) if dx else math.inf
    ty = (h / 2) / abs(dy) if dy else math.inf
    t = min(tx, ty)
    return x0 + dx * t, y0 + dy * t


# --------------------------------------------------------------------------
# the pick-and-place state machine, and one scripted run of it
# --------------------------------------------------------------------------

# The transition table: (state, event) -> next state. The retry rule on CHECK GRASP
# needs the try counter, so it is handled in fsm_step below.
FSM_TABLE: dict[tuple[str, str], str] = {
    ('DETECT', 'mug found'): 'APPROACH',
    ('DETECT', 'no mug left'): 'DONE',
    ('APPROACH', 'arrived'): 'GRASP',
    ('APPROACH', 'no path'): 'ASK FOR HELP',
    ('GRASP', 'gripper closed'): 'CHECK GRASP',
    ('CHECK GRASP', 'holding'): 'LIFT',
    ('LIFT', 'lifted'): 'CARRY',
    ('CARRY', 'at the bin'): 'RELEASE',
    ('CARRY', 'dropped'): 'ASK FOR HELP',
    ('RELEASE', 'gripper open'): 'HOME',
    ('HOME', 'at home'): 'DETECT',
}
MAX_TRIES: int = 3

# How long the arm spends in each state, in seconds, for the scripted run.
FSM_SECONDS: dict[str, float] = {
    'DETECT': 0.4, 'APPROACH': 2.0, 'GRASP': 1.0, 'CHECK GRASP': 0.2, 'LIFT': 0.8,
    'CARRY': 2.5, 'RELEASE': 0.5, 'HOME': 2.0,
}


def fsm_step(state: str, event: str, tries: int) -> tuple[str, int]:
    """One transition. Returns the next state and the new try counter."""
    if state == 'CHECK GRASP' and event == 'empty':
        tries += 1
        return ('DETECT', tries) if tries < MAX_TRIES else ('ASK FOR HELP', tries)
    nxt: str = FSM_TABLE[(state, event)]
    if state == 'CHECK GRASP' and event == 'holding':
        tries = 0
    return nxt, tries


def fsm_run() -> list[tuple[float, float, str, str]]:
    """Two mugs; the first grasp on mug 1 closes on nothing. Returns (start, end,
    state, event that ended it) for every state visited."""
    grasp_results: list[str] = ['empty', 'holding', 'holding']
    mugs_left: int = 2
    state, tries, t = 'DETECT', 0, 0.0
    log: list[tuple[float, float, str, str]] = []
    while state not in ('DONE', 'ASK FOR HELP'):
        if state == 'DETECT':
            event = 'mug found' if mugs_left > 0 else 'no mug left'
        elif state == 'CHECK GRASP':
            event = grasp_results.pop(0)
        elif state == 'RELEASE':
            event = 'gripper open'
            mugs_left -= 1
        else:
            event = {'APPROACH': 'arrived', 'GRASP': 'gripper closed', 'LIFT': 'lifted',
                     'CARRY': 'at the bin', 'HOME': 'at home'}[state]
        dt: float = FSM_SECONDS[state]
        log.append((t, t + dt, state, f'{event}' + (f' (tries = {tries + 1})'
                                                   if event == 'empty' else '')))
        t += dt
        state, tries = fsm_step(state, event, tries)
    log.append((t, t, state, ''))
    return log


# --------------------------------------------------------------------------
# a small behaviour tree engine, and the pick-and-place tree
# --------------------------------------------------------------------------

@dataclass
class Node:
    name: str
    kind: str                      # 'sequence', 'fallback', 'retry', 'action', 'condition'
    children: list['Node'] = field(default_factory=list)
    ticks: int = 0                 # actions: how many ticks one run takes
    outcomes: list[str] = field(default_factory=list)   # actions, conditions: results in turn
    limit: int = 0                 # retry: how many tries
    # running state
    index: int = 0
    count: int = 0
    elapsed: int = 0
    calls: int = 0

    def reset(self) -> None:
        self.index = 0
        self.elapsed = 0
        for c in self.children:
            c.reset()


def bt_tick(node: Node, seen: dict[str, str]) -> str:
    """Tick one node and, through it, its children. Record every answer in seen."""
    status: str
    if node.kind == 'condition':
        status = node.outcomes[min(node.calls, len(node.outcomes) - 1)]
        node.calls += 1
    elif node.kind == 'action':
        node.elapsed += 1
        if node.elapsed < node.ticks:
            status = RUNNING
        else:
            status = node.outcomes[min(node.calls, len(node.outcomes) - 1)]
            node.calls += 1
            node.elapsed = 0
    elif node.kind in ('sequence', 'fallback'):
        # Both remember which child was running, and carry on from it.
        go_on: str = SUCCESS if node.kind == 'sequence' else FAILURE
        status = go_on
        while node.index < len(node.children):
            s = bt_tick(node.children[node.index], seen)
            if s == RUNNING:
                status = RUNNING
                break
            if s != go_on:
                status = s
                node.reset()
                break
            node.index += 1
        if status != RUNNING:
            node.reset()
    elif node.kind == 'retry':
        s = bt_tick(node.children[0], seen)
        if s == FAILURE:
            node.count += 1
            node.children[0].reset()
            if node.count < node.limit:
                status = RUNNING
            else:
                node.count = 0
                status = FAILURE
        else:
            if s == SUCCESS:
                node.count = 0
            status = s
    else:
        raise ValueError(node.kind)
    seen[node.name] = status
    return status


def pick_tree(holding: list[str]) -> Node:
    """The pick-and-place tree of the behaviour tree page. holding gives the answer
    of the 'holding mug?' check on each try."""
    located = Node('mug located', 'fallback', [
        Node('mug pose known?', 'condition', outcomes=[FAILURE, SUCCESS]),
        Node('detect mug', 'action', ticks=4, outcomes=[SUCCESS]),
    ])
    grasp = Node('grasp', 'sequence', [
        Node('open gripper', 'action', ticks=2, outcomes=[SUCCESS]),
        Node('move above mug', 'action', ticks=15, outcomes=[SUCCESS]),
        Node('lower and close', 'action', ticks=8, outcomes=[SUCCESS]),
        Node('holding mug?', 'condition', outcomes=holding),
    ])
    pick_place = Node('pick and place', 'sequence', [
        located,
        Node('retry x3', 'retry', [grasp], limit=3),
        Node('move to bin', 'action', ticks=20, outcomes=[SUCCESS]),
        Node('release', 'action', ticks=3, outcomes=[SUCCESS]),
    ])
    return Node('task', 'fallback', [pick_place,
                                     Node('ask for help', 'action', ticks=1,
                                          outcomes=[SUCCESS])])


def all_nodes(n: Node) -> list[Node]:
    out: list[Node] = [n]
    for c in n.children:
        out += all_nodes(c)
    return out


def bt_run(holding: list[str]) -> tuple[Node, list[dict[str, str]]]:
    """Tick the tree at 10 Hz until the root stops running. Returns the tree and, for
    every tick, the answer of each node that was ticked."""
    root = pick_tree(holding)
    trace: list[dict[str, str]] = []
    while True:
        seen: dict[str, str] = {}
        s = bt_tick(root, seen)
        trace.append(seen)
        if s != RUNNING:
            return root, trace


# --------------------------------------------------------------------------
# drawing a behaviour tree
# --------------------------------------------------------------------------

NODE_W: float = 1.75
NODE_H: float = 0.72


def _layout(root: Node, dx: float = 2.0, dy: float = 1.5) -> dict[str, tuple[float, float]]:
    """Leaves side by side in order; each parent above the middle of its children."""
    pos: dict[str, tuple[float, float]] = {}
    next_x: list[float] = [0.0]

    def place(n: Node, depth: int) -> float:
        if not n.children:
            x = next_x[0]
            next_x[0] += dx
        else:
            xs = [place(c, depth + 1) for c in n.children]
            x = (xs[0] + xs[-1]) / 2
        pos[n.name] = (x, -depth * dy)
        return x

    place(root, 0)
    return pos


def _draw_node(ax: Axes, n: Node, x: float, y: float, edge: str = INK,
               fill: str = 'white', size: float = 9, lw: float = 1.6,
               w: float = NODE_W) -> None:
    h = NODE_H
    if n.kind == 'condition':
        ax.add_patch(Ellipse((x, y), w, h, facecolor=fill, edgecolor=edge, lw=lw,
                             zorder=6))
        _label(ax, x, y, n.name.replace(' ', '\n', 1) if len(n.name) > 12 else n.name,
               size=size)
    elif n.kind == 'action':
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fill,
                               edgecolor=edge, lw=lw, zorder=6))
        _label(ax, x, y, n.name.replace(' ', '\n', 1) if len(n.name) > 12 else n.name,
               size=size)
    elif n.kind == 'retry':
        pts = [(x - w / 2 + 0.2, y - h / 2), (x + w / 2 - 0.2, y - h / 2),
               (x + w / 2, y), (x + w / 2 - 0.2, y + h / 2),
               (x - w / 2 + 0.2, y + h / 2), (x - w / 2, y)]
        ax.add_patch(Polygon(pts, closed=True, facecolor=fill, edgecolor=edge, lw=lw,
                             zorder=6))
        _label(ax, x, y, 'retry\nup to 3 times', size=size - 0.5)
    else:
        sym = '→' if n.kind == 'sequence' else '?'
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fill,
                               edgecolor=edge, lw=lw, zorder=6))
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), 0.42, h, facecolor=LINK_PALE,
                               edgecolor=edge, lw=lw, zorder=6))
        _label(ax, x - w / 2 + 0.21, y, sym, size=size + 3, weight='bold')
        name = n.name.replace(' ', '\n', 1) if len(n.name) > 9 else n.name
        _label(ax, x + 0.21, y, name, size=size)


def _draw_tree(ax: Axes, root: Node, pos: dict[str, tuple[float, float]],
               colours: dict[str, str] | None = None,
               highlight: set[str] | None = None, size: float = 9,
               w: float = NODE_W) -> None:
    for n in all_nodes(root):
        x, y = pos[n.name]
        for c in n.children:
            cx, cy = pos[c.name]
            ax.plot([x, cx], [y - NODE_H / 2, cy + NODE_H / 2], color=MUTED, lw=1.3,
                    zorder=2)
    for n in all_nodes(root):
        x, y = pos[n.name]
        fill, edge, lw = 'white', INK, 1.6
        if colours is not None:
            if n.name in colours:
                fill = STATUS_COLOUR[colours[n.name]] + '55'
                edge = STATUS_COLOUR[colours[n.name]]
                lw = 2.4
            else:
                edge = GRID
        if highlight and n.name in highlight:
            fill, edge, lw = PURPLE + '30', PURPLE, 2.4
        _draw_node(ax, n, x, y, edge=edge, fill=fill, size=size, lw=lw, w=w)


# --------------------------------------------------------------------------
# 01_overview
# --------------------------------------------------------------------------

OVERVIEW: str = 'overview'

# The table seen from above, in decimetres: 10 wide and 7 deep.
MUGS: list[tuple[float, float]] = [(2.2, 5.6), (3.6, 3.4), (5.2, 5.9), (6.6, 2.4),
                                   (8.2, 5.0)]
SLOTS: list[tuple[float, float]] = [(1.2 + 0.9 * i, 0.8) for i in range(5)]
VIEWS: list[tuple[float, float]] = [(2.2, 4.6), (4.4, 4.9), (7.4, 3.8), (5.4, 2.6),
                                    (8.4, 5.8), (3.0, 2.4)]
VIEW_R: float = 1.7


def greedy_views() -> list[int]:
    """Greedy set cover: keep taking the view that sees the most mugs not yet seen."""
    sees: list[set[int]] = [{m for m, (mx, my) in enumerate(MUGS)
                             if math.hypot(mx - vx, my - vy) <= VIEW_R}
                            for vx, vy in VIEWS]
    left: set[int] = set(range(len(MUGS)))
    chosen: list[int] = []
    while left:
        best = max(range(len(VIEWS)), key=lambda v: (len(sees[v] & left), -v))
        if not sees[best] & left:
            break
        chosen.append(best)
        left -= sees[best]
    return chosen


def best_assignment() -> tuple[tuple[int, ...], float]:
    """Try every way of putting the five mugs in the five slots; keep the shortest."""
    best: tuple[tuple[int, ...], float] = ((), math.inf)
    for perm in itertools.permutations(range(len(SLOTS))):
        d = sum(math.dist(MUGS[m], SLOTS[s]) for m, s in enumerate(perm))
        if d < best[1]:
            best = (perm, d)
    return best


def four_questions() -> None:
    """One table, and the question each of the four techniques answers on it."""
    fig, ax = plt.subplots(figsize=(13.0, 6.4), facecolor='white')
    _axes(ax, (-0.4, 17.2), (-0.9, 7.6))
    ax.add_patch(Rectangle((0, 0), 10, 7, facecolor=TABLE, edgecolor=INK, lw=1.2,
                           zorder=1))
    # the tray of five slots
    ax.add_patch(Rectangle((0.7, 0.35), 4.5, 0.9, facecolor='white', edgecolor=MUTED,
                           lw=1.2, zorder=2))
    for sx, sy in SLOTS:
        ax.add_patch(Circle((sx, sy), 0.3, facecolor='none', edgecolor=MUTED, lw=1.2,
                            ls='--', zorder=3))
    _label(ax, 2.95, 0.02, 'tray', size=9, color=MUTED, va='top')
    # the views the greedy rule chose
    for v in greedy_views():
        vx, vy = VIEWS[v]
        ax.add_patch(Circle((vx, vy), VIEW_R, facecolor=LINK_PALE, edgecolor=LINK,
                            lw=1.6, alpha=0.45, zorder=2))
        ax.plot(vx, vy, marker='+', color=LINK, ms=10, mew=2, zorder=4)
    # the mugs, and the assignment to slots
    perm, _ = best_assignment()
    for m, (mx, my) in enumerate(MUGS):
        sx, sy = SLOTS[perm[m]]
        _arrow(ax, (mx, my - 0.35), (sx, sy + 0.32), color=PURPLE, lw=1.4, ls='--', z=3)
    for m, (mx, my) in enumerate(MUGS):
        ax.add_patch(Circle((mx, my), 0.33, facecolor=GRIP if m == 1 else LINK,
                            edgecolor=INK, lw=1.0, zorder=5))
    # the failed grasp on mug 2
    mx, my = MUGS[1]
    ax.add_patch(Circle((mx, my), 0.6, facecolor='none', edgecolor=GRIP, lw=2.2,
                        zorder=6))
    # number tags
    tags: list[tuple[float, float, str]] = [(mx - 0.95, my + 0.2, '1'),
                                            (VIEWS[1][0] - 1.2, VIEWS[1][1] + 1.2, '2'),
                                            (6.0, 1.3, '3')]
    for tx, ty, t in tags:
        ax.add_patch(Circle((tx, ty), 0.28, facecolor=INK, edgecolor='none', zorder=8))
        _label(ax, tx, ty, t, size=10, color='white', weight='bold')
    # the notes on the right
    notes: list[tuple[str, str, str]] = [
        ('1', 'What now, and what if it fails?',
         'The grasp on the red mug closed on\nnothing. Try again, or ask for help?\n'
         'A state machine or a behaviour\ntree decides, many times a second.'),
        ('2', 'Which camera views?',
         'Blue circles: the views the greedy\nrule chose so that every mug is\n'
         'seen at least once (greedy set cover).'),
        ('3', 'Which mug goes in which slot?',
         'Dashed purple lines: the pairing with\nthe shortest total distance, found by\n'
         'trying every pairing (a solver’s job).'),
    ]
    y = 6.9
    for t, head, body in notes:
        ax.add_patch(Circle((10.9, y - 0.05), 0.28, facecolor=INK, edgecolor='none'))
        _label(ax, 10.9, y - 0.05, t, size=10, color='white', weight='bold')
        _label(ax, 11.4, y, head, size=11, ha='left', weight='bold')
        _label(ax, 11.4, y - 0.4, body, size=9.5, ha='left', va='top', color=INK)
        y -= 2.45
    _caption(ax, 5.0, -0.35, 'The table from above, with five mugs and a tray.')
    _save(fig, OVERVIEW, 'four-questions-one-table.svg')


def when_each_runs() -> None:
    """Along one real run: the task logic ticks all the time, the choosers run once."""
    log = fsm_run()
    end: float = log[-1][1]
    fig, ax = plt.subplots(figsize=(13.5, 4.6), facecolor='white')
    ax.set_facecolor('white')
    rows: dict[str, float] = {'task logic\n(state machine or\nbehaviour tree)': 2.0,
                              'greedy set cover': 1.0, 'optimisation solver': 0.0}
    colours: dict[str, str] = {'DETECT': LINK, 'APPROACH': LINK_PALE, 'GRASP': JOINT,
                               'CHECK GRASP': GRIP, 'LIFT': '#8fd19e', 'CARRY': SLIDE,
                               'RELEASE': WRIST, 'HOME': GRID}
    for s0, s1, st, _ev in log[:-1]:
        ax.add_patch(Rectangle((s0, 1.72), s1 - s0, 0.56, facecolor=colours[st],
                               edgecolor='white', lw=0.8, zorder=2))
    for k in range(int(end * 10) + 1):
        ax.plot([k / 10, k / 10], [2.3, 2.42], color=INK, lw=0.5, zorder=3)
    _label(ax, end + 0.2, 2.36, 'checked every 0.1 s', size=9, ha='left', color=MUTED)
    # a key to the state colours, under the time axis
    handles = [Rectangle((0, 0), 1, 1, facecolor=c, edgecolor='none')
               for c in colours.values()]
    ax.legend(handles, [s.lower() for s in colours], loc='upper center',
              bbox_to_anchor=(0.5, -0.2), ncol=len(colours), frameon=False, fontsize=9,
              handlelength=1.4, columnspacing=1.2)
    # the failed grasp
    fail = next(r for r in log if r[3].startswith('empty'))
    ax.annotate('grasp closed on nothing:\ntry again', xy=(fail[1], 2.28),
                xytext=(fail[1] + 1.5, 3.05), fontsize=9, color=GRIP, ha='left',
                va='center', arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.4})
    for (name, y), (t, text) in zip(list(rows.items())[1:],
                                    [(0.0, 'choose camera views\nonce, at the start'),
                                     (0.05, 'pair mugs with slots\nonce, at the start')]):
        ax.plot(t, y, marker='D', color=PURPLE if y == 0 else LINK, ms=11, zorder=4)
        _label(ax, t + 0.35, y, text, size=9, ha='left')
    ax.set_yticks(list(rows.values()))
    ax.set_yticklabels(list(rows.keys()), fontsize=10)
    ax.set_ylim(-0.6, 3.5)
    ax.set_xlim(-0.3, end + 2.2)
    ax.set_xlabel('time (seconds)', fontsize=10)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, lw=0.6, zorder=0)
    _save(fig, OVERVIEW, 'when-each-one-runs.svg')


# --------------------------------------------------------------------------
# 02_finite-state-machines
# --------------------------------------------------------------------------

FSM: str = 'finite-state-machines'

FSM_POS: dict[str, tuple[float, float]] = {
    'DETECT': (0.0, 3.4), 'APPROACH': (3.6, 3.4), 'GRASP': (7.2, 3.4),
    'CHECK GRASP': (10.8, 3.4),
    'HOME': (0.0, 0.0), 'RELEASE': (3.6, 0.0), 'CARRY': (7.2, 0.0), 'LIFT': (10.8, 0.0),
    'ASK FOR HELP': (5.4, 1.7), 'DONE': (-3.3, 3.4),
}
BOX_W: float = 2.0
BOX_H: float = 0.72


def _fsm_edge(ax: Axes, a: str, b: str, text: str, color: str = INK, rad: float = 0.0,
              lpos: tuple[float, float] | None = None, tsize: float = 9) -> None:
    ax0, ay0 = FSM_POS[a]
    bx0, by0 = FSM_POS[b]
    p = _edge_point(ax0, ay0, bx0, by0, BOX_W, BOX_H)
    q = _edge_point(bx0, by0, ax0, ay0, BOX_W, BOX_H)
    _arrow(ax, p, q, color=color, lw=1.6, rad=rad)
    if lpos is None:
        lpos = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    _label(ax, lpos[0], lpos[1], text, size=tsize, color=color, box=True)


def state_graph() -> None:
    """The pick-and-place state machine, drawn from its transition table."""
    fig, ax = plt.subplots(figsize=(13.5, 6.4), facecolor='white')
    _axes(ax, (-4.6, 12.2), (-1.0, 5.6))
    for s, (x, y) in FSM_POS.items():
        color = {'ASK FOR HELP': GRIP, 'DONE': SLIDE}.get(s, LINK)
        _state_box(ax, x, y, s.lower(), color=color, w=BOX_W, h=BOX_H)
    # start arrow
    _arrow(ax, (0.0, 4.6), (0.0, 3.4 + BOX_H / 2), color=INK, lw=1.8)
    ax.plot(0.0, 4.6, marker='o', color=INK, ms=9)
    _label(ax, 0.25, 4.65, 'start', size=9, ha='left')
    # the happy path
    _fsm_edge(ax, 'DETECT', 'APPROACH', 'mug found', lpos=(1.8, 3.62))
    _fsm_edge(ax, 'APPROACH', 'GRASP', 'arrived', lpos=(5.4, 3.62))
    _fsm_edge(ax, 'GRASP', 'CHECK GRASP', 'gripper\nclosed', lpos=(9.0, 3.75))
    _fsm_edge(ax, 'CHECK GRASP', 'LIFT', 'holding\n(tries = 0)', lpos=(11.55, 1.7))
    _fsm_edge(ax, 'LIFT', 'CARRY', 'lifted', lpos=(9.0, -0.22))
    _fsm_edge(ax, 'CARRY', 'RELEASE', 'at the bin', lpos=(5.4, -0.22))
    _fsm_edge(ax, 'RELEASE', 'HOME', 'gripper open', lpos=(1.8, -0.22))
    _fsm_edge(ax, 'HOME', 'DETECT', 'at home', lpos=(-0.55, 1.7))
    _fsm_edge(ax, 'DETECT', 'DONE', 'no mug\nleft', color=SLIDE, lpos=(-1.65, 3.8))
    # the retry loop over the top
    _arrow(ax, (10.8, 3.4 + BOX_H / 2), (0.35, 3.4 + BOX_H / 2), color=WRIST, lw=1.8,
           rad=0.18)
    _label(ax, 5.4, 5.05, 'empty and tries < 3:  tries = tries + 1, look again',
           size=9.5, color=WRIST, box=True)
    # the ways to give up
    _fsm_edge(ax, 'CHECK GRASP', 'ASK FOR HELP', 'empty and\ntries = 3', color=GRIP,
              lpos=(8.3, 2.3))
    _fsm_edge(ax, 'APPROACH', 'ASK FOR HELP', 'no path', color=GRIP, lpos=(4.25, 2.55))
    _fsm_edge(ax, 'CARRY', 'ASK FOR HELP', 'dropped', color=GRIP, lpos=(6.55, 0.85))
    _caption(ax, 3.8, -0.75, 'Boxes are states. Arrows are transitions, labelled with '
             'the event that fires them.')
    _save(fig, FSM, 'pick-and-place-states.svg')


def run_trace() -> None:
    """Which state the machine was in, second by second, during the scripted run."""
    log = fsm_run()
    order: list[str] = ['DETECT', 'APPROACH', 'GRASP', 'CHECK GRASP', 'LIFT', 'CARRY',
                        'RELEASE', 'HOME', 'DONE']
    ypos = {s: len(order) - 1 - i for i, s in enumerate(order)}
    fig, ax = plt.subplots(figsize=(13.5, 5.2), facecolor='white')
    ax.set_facecolor('white')
    xs: list[float] = []
    ys: list[float] = []
    for s0, s1, st, _ev in log:
        xs += [s0, s1]
        ys += [ypos[st], ypos[st]]
        ax.plot([s0, s1], [ypos[st], ypos[st]], color=LINK, lw=6, solid_capstyle='butt',
                zorder=3)
    ax.plot(xs, ys, color=LINK, lw=1.0, zorder=2)
    end: float = log[-1][0]
    ax.plot(end, ypos['DONE'], marker='o', color=SLIDE, ms=10, zorder=4)
    fail = next(r for r in log if r[3].startswith('empty'))
    ax.annotate('empty, tries = 1:\nback to detect', xy=(fail[1], ypos['CHECK GRASP']),
                xytext=(fail[1] + 1.0, ypos['DETECT'] + 0.85), fontsize=9.5,
                color=WRIST, ha='left', va='center',
                arrowprops={'arrowstyle': '-|>', 'color': WRIST, 'lw': 1.4})
    mug_ends = [r[1] for r in log if r[2] == 'RELEASE']
    for i, t in enumerate(mug_ends):
        ax.axvline(t, color=SLIDE, lw=1.0, ls='--', zorder=1)
        _label(ax, t + 0.1, len(order) - 0.15, f'mug {i + 1} in the bin\n{t:.1f} s',
               size=9, ha='left', color=SLIDE)
    _label(ax, end - 0.3, ypos['DONE'] - 0.6, f'done at {end:.1f} s', size=9.5,
           ha='right', color=SLIDE)
    ax.set_yticks(list(ypos.values()))
    ax.set_yticklabels([s.lower() for s in ypos], fontsize=10)
    ax.set_ylim(-1.1, len(order) + 0.4)
    ax.set_xlim(-0.3, end + 1.0)
    ax.set_xlabel('time (seconds)', fontsize=10)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.grid(axis='x', color=GRID, lw=0.6, zorder=0)
    _save(fig, FSM, 'one-run-over-time.svg')


def flat_vs_nested() -> None:
    """A stop button: an arrow from every state, or one arrow from a parent state."""
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 6.0), facecolor='white')
    names: list[str] = ['detect', 'approach', 'grasp', 'check\ngrasp', 'lift', 'carry',
                        'release', 'home']
    grid_pos: list[tuple[float, float]] = [(0, 3.6), (2.4, 3.6), (4.8, 3.6), (7.2, 3.6),
                                           (7.2, 0.6), (4.8, 0.6), (2.4, 0.6), (0, 0.6)]
    w, h = 1.7, 0.66
    for k, ax in enumerate(axes):
        stop: tuple[float, float] = (3.6, 2.1) if k == 0 else (3.6, -1.7)
        _axes(ax, (-1.4, 8.6), (-2.6, 5.6))
        for i, ((x, y), n) in enumerate(zip(grid_pos, names)):
            _state_box(ax, x, y, n, w=w, h=h, size=9)
            a, b = grid_pos[i], grid_pos[(i + 1) % len(grid_pos)]
            p = _edge_point(a[0], a[1], b[0], b[1], w, h)
            q = _edge_point(b[0], b[1], a[0], a[1], w, h)
            _arrow(ax, p, q, color=MUTED, lw=1.3)
        _state_box(ax, stop[0], stop[1], 'stopped', color=GRIP, w=w, h=h, size=9)
        if k == 0:
            for (x, y) in grid_pos:
                p = _edge_point(x, y, stop[0], stop[1], w, h)
                q = _edge_point(stop[0], stop[1], x, y, w, h)
                _arrow(ax, p, q, color=GRIP, lw=1.2)
            _title(ax, 3.6, 5.3, 'Flat: 8 new arrows for one button')
            _caption(ax, 3.6, 4.9, 'and "resume" needs 8 more, one back to each state',
                     size=9.5)
        else:
            ax.add_patch(FancyBboxPatch((-1.1, 0.05), 9.4, 4.1,
                                        boxstyle='round,pad=0.02,rounding_size=0.3',
                                        facecolor='none', edgecolor=LINK, lw=2.0,
                                        ls='--', zorder=1))
            _label(ax, -0.95, 4.4, 'working', size=10, ha='left', color=LINK,
                   weight='bold')
            _arrow(ax, (3.2, 0.05), (3.2, stop[1] + h / 2), color=GRIP, lw=1.8)
            _label(ax, 3.05, -0.75, 'stop\npressed', size=9, ha='right', color=GRIP)
            _arrow(ax, (4.0, stop[1] + h / 2), (4.0, 0.05), color=SLIDE, lw=1.8)
            _label(ax, 4.15, -0.75, 'resume: back to the\nstate it was in (H)', size=9,
                   ha='left', color=SLIDE)
            ax.add_patch(Circle((4.0, 0.05), 0.2, facecolor='white', edgecolor=SLIDE,
                                lw=1.6, zorder=7))
            _label(ax, 4.0, 0.05, 'H', size=8, color=SLIDE, weight='bold')
            _title(ax, 3.6, 5.3, 'Nested: 1 arrow out, 1 arrow back')
            _caption(ax, 3.6, 4.9, 'all eight states sit inside one parent state',
                     size=9.5)
    _save(fig, FSM, 'flat-or-nested-stop.svg')


def retry_limit() -> None:
    """How the retry limit changes the chance of finishing, for a 70 % grasp."""
    p: float = 0.7
    limits = np.arange(1, 6)
    ok = 1 - (1 - p) ** limits
    fig, ax = plt.subplots(figsize=(9.0, 4.6), facecolor='white')
    ax.set_facecolor('white')
    bars = ax.bar(limits, ok * 100, color=[LINK if k != 3 else WRIST for k in limits],
                  width=0.6, zorder=3)
    for b, v in zip(bars, ok):
        ax.text(b.get_x() + b.get_width() / 2, v * 100 + 1.2, f'{v * 100:.1f} %',
                ha='center', va='bottom', fontsize=10, color=INK)
    ax.set_ylim(0, 116)
    ax.set_xticks(limits)
    ax.set_xticklabels([f'{k}' for k in limits], fontsize=10)
    ax.set_xlabel('most tries allowed before "ask for help"', fontsize=10)
    ax.set_ylabel('mugs picked without help (%)', fontsize=10)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.grid(axis='y', color=GRID, lw=0.6, zorder=0)
    _label(ax, 3.0, 110, 'the limit used on this page', size=9.5, color=WRIST)
    _save(fig, FSM, 'retry-limit.svg')


# --------------------------------------------------------------------------
# 03_behaviour-trees
# --------------------------------------------------------------------------

BT: str = 'behaviour-trees'


def tree_picture() -> None:
    """The pick-and-place behaviour tree, with a key to the node shapes."""
    root = pick_tree([FAILURE, SUCCESS])
    pos = _layout(root)
    xs = [p[0] for p in pos.values()]
    fig, ax = plt.subplots(figsize=(15.0, 7.4), facecolor='white')
    _axes(ax, (min(xs) - 1.2, max(xs) + 1.2), (-8.9, 0.8))
    _draw_tree(ax, root, pos)
    # the order in which leaves run, as small numbers
    order = ['mug pose known?', 'detect mug', 'open gripper', 'move above mug',
             'lower and close', 'holding mug?', 'move to bin', 'release', 'ask for help']
    for i, name in enumerate(order):
        x, y = pos[name]
        _label(ax, x, y - NODE_H / 2 - 0.25, f'({i + 1})', size=8.5, color=MUTED)
    # key, in two rows
    key = [(Node('sequence', 'sequence'), 'Sequence: runs its children left to right,\n'
            'and stops at the first failure'),
           (Node('action', 'action'), 'Action: does something;\nit may take many ticks'),
           (Node('fallback', 'fallback'), 'Fallback: tries its children left to right,\n'
            'and stops at the first success'),
           (Node('check?', 'condition'), 'Condition: a yes-or-no check\nthat answers at once')]
    for i, (n, text) in enumerate(key):
        kx = min(xs) + 0.4 + (i % 2) * 7.5
        ky = -7.35 - (i // 2) * 1.0
        _draw_node(ax, n, kx, ky, size=8.5)
        _label(ax, kx + NODE_W / 2 + 0.2, ky, text, size=9, ha='left')
    ax.plot([min(xs) - 1.0, max(xs) + 1.0], [-6.75, -6.75], color=GRID, lw=1.0)
    _save(fig, BT, 'pick-and-place-tree.svg')


def how_answers_combine() -> None:
    """Three small cases: how a Sequence and a Fallback turn children's answers into one."""
    cases: list[tuple[str, list[str | None], str, str]] = [
        ('sequence', [SUCCESS, FAILURE, None], FAILURE,
         'Sequence: the 2nd child failed,\nso the 3rd is not ticked'),
        ('sequence', [SUCCESS, RUNNING, None], RUNNING,
         'Sequence: the 2nd child is still\nrunning, so the Sequence is too'),
        ('fallback', [FAILURE, SUCCESS, None], SUCCESS,
         'Fallback: the 2nd child worked,\nso the 3rd is not needed'),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14.0, 4.6), facecolor='white')
    for ax, (kind, kids, result, text) in zip(axes, cases):
        _axes(ax, (-3.9, 3.9), (-3.6, 1.2))
        parent = Node(kind, kind, [Node(f'child {i + 1}', 'action') for i in range(3)])
        pos = {parent.name: (0.0, 0.0)}
        for i, c in enumerate(parent.children):
            pos[c.name] = (-2.55 + 2.55 * i, -1.9)
        colours = {parent.name: result}
        for c, s in zip(parent.children, kids):
            if s is not None:
                colours[c.name] = s
        _draw_tree(ax, parent, pos, colours=colours, size=9, w=2.3)
        for c, s in zip(parent.children, kids):
            x, y = pos[c.name]
            _label(ax, x, y - 0.62, s.lower() if s else 'not ticked', size=9,
                   color=STATUS_COLOUR[s] if s else MUTED, weight='bold')
        _label(ax, 1.3, 0.62, result.lower(), size=9.5, color=STATUS_COLOUR[result],
               weight='bold', ha='left')
        _caption(ax, 0.0, -2.9, text, size=10)
    _save(fig, BT, 'how-answers-combine.svg')


def tick_trace() -> None:
    """Every node's answer on every tick of the real run, with the first grasp empty."""
    root, trace = bt_run([FAILURE, SUCCESS])
    nodes = all_nodes(root)
    fig, ax = plt.subplots(figsize=(14.5, 6.4), facecolor='white')
    ax.set_facecolor('white')
    for r, n in enumerate(nodes):
        y = len(nodes) - 1 - r
        for t, seen in enumerate(trace):
            if n.name in seen:
                ax.add_patch(Rectangle((t, y - 0.4), 0.92, 0.8,
                                       facecolor=STATUS_COLOUR[seen[n.name]],
                                       edgecolor='none', zorder=3))
            else:
                ax.add_patch(Rectangle((t, y - 0.4), 0.92, 0.8, facecolor='#f4f4f4',
                                       edgecolor='none', zorder=2))
    depth: dict[str, int] = {}

    def walk(n: Node, d: int) -> None:
        depth[n.name] = d
        for c in n.children:
            walk(c, d + 1)
    walk(root, 0)
    ax.set_yticks([len(nodes) - 1 - r for r in range(len(nodes))])
    ax.set_yticklabels(['   ' * depth[n.name] + n.name for n in nodes], fontsize=9.5,
                       family='monospace')
    ax.set_xlim(-0.5, len(trace) + 0.5)
    ax.set_ylim(-1.6, len(nodes) + 0.3)
    ticks = [1] + list(range(10, len(trace) + 1, 10))
    ax.set_xticks([t - 1 + 0.46 for t in ticks])
    ax.set_xticklabels([f'{t}' for t in ticks], fontsize=9)
    ax.set_xlabel('tick number (10 ticks a second, so tick 70 ends at 7.0 s)', fontsize=10)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis='y', length=0)
    # mark the failed check
    t_fail = next(t for t, s in enumerate(trace) if s.get('holding mug?') == FAILURE)
    y_hold = len(nodes) - 1 - [n.name for n in nodes].index('holding mug?')
    ax.annotate('empty: the Retry starts\nthe grasp again', xy=(t_fail + 0.46, y_hold - 0.4),
                xytext=(t_fail + 4, -1.0), fontsize=9.5, color=GRIP, ha='left',
                va='center', arrowprops={'arrowstyle': '-|>', 'color': GRIP, 'lw': 1.4})
    x0: float = len(trace) - 26
    for i, (s, c) in enumerate(STATUS_COLOUR.items()):
        ax.add_patch(Rectangle((x0 + 9 * i, -1.3), 0.9, 0.6, facecolor=c,
                               edgecolor='none'))
        ax.text(x0 + 9 * i + 1.3, -1.0, s.lower(), fontsize=9, va='center')
    _save(fig, BT, 'every-tick-of-one-run.svg')


def add_a_recovery() -> None:
    """Adding 'nudge the mug and look again' is one new subtree; nothing else changes."""
    def before() -> Node:
        return Node('retry x3', 'retry', [
            Node('grasp', 'sequence', [
                Node('open gripper', 'action'), Node('move above mug', 'action'),
                Node('lower and close', 'action'), Node('holding mug?', 'condition')])])

    def after() -> Node:
        return Node('retry x3', 'retry', [
            Node('grasp or recover', 'fallback', [
                Node('grasp', 'sequence', [
                    Node('open gripper', 'action'), Node('move above mug', 'action'),
                    Node('lower and close', 'action'), Node('holding mug?', 'condition')]),
                Node('recover', 'sequence', [
                    Node('nudge mug to centre', 'action'),
                    Node('detect mug', 'action'), Node('fail (try again)', 'action')])])])

    fig, axes = plt.subplots(1, 2, figsize=(16.0, 5.8), facecolor='white',
                             gridspec_kw={'width_ratios': [1.0, 1.75]})
    for k, (ax, tree) in enumerate(zip(axes, [before(), after()])):
        pos = _layout(tree, dx=1.95, dy=1.45)
        xs = [p[0] for p in pos.values()]
        _axes(ax, (min(xs) - 1.1, max(xs) + 1.1), (-4.9, 1.2))
        new = {'grasp or recover', 'recover', 'nudge mug to centre', 'detect mug',
               'fail (try again)'} if k else set()
        _draw_tree(ax, tree, pos, highlight=new, size=8)
        _title(ax, (min(xs) + max(xs)) / 2, 1.0,
               'Before' if k == 0 else 'After: one new branch (purple)')
    _save(fig, BT, 'add-a-recovery.svg')


# --------------------------------------------------------------------------

def print_traces() -> None:
    print('state machine run:')
    for s0, s1, st, ev in fsm_run():
        print(f'  {s0:5.1f} -> {s1:5.1f}  {st:12s}  {ev}')
    print('greedy views:', greedy_views(), [VIEWS[v] for v in greedy_views()])
    perm, d = best_assignment()
    print('best assignment:', perm, f'{d:.2f} dm')
    for limit in range(1, 6):
        print(f'  tries {limit}: {1 - 0.3 ** limit:.4f}')
    root, trace = bt_run([FAILURE, SUCCESS])
    print('behaviour tree ticks:', len(trace))
    for t, seen in enumerate(trace):
        brief = {k: v[0] for k, v in seen.items()}
        print(f'  {t + 1:3d} {brief}')
    root, trace = bt_run([FAILURE, FAILURE, FAILURE])
    print('three empty grasps, ticks:', len(trace), 'last:', trace[-1])


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if '--trace' in sys.argv:
        print_traces()
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    four_questions()
    when_each_runs()
    state_graph()
    run_trace()
    flat_vs_nested()
    retry_limit()
    tree_picture()
    how_answers_combine()
    tick_trace()
    add_a_recovery()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
