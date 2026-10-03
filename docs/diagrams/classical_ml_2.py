"""Generate the diagrams for two pages of docs/07_learned-models/02_classical-machine-learning/.

    02_most-used/02_decision-trees-and-forests.md
        -> images/classical-machine-learning/decision-trees-and-forests/
    03_also-used/04_support-vector-machines.md
        -> images/classical-machine-learning/support-vector-machines/

Run with:  pixi run python ../docs/diagrams/classical_ml_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file, and the script prints
them so the documents can quote the same values. The data is simulated from
made-up rules, so that the true answer is known. The methods are real and
written in NumPy: a decision tree (CART, split by the Gini impurity), a random
forest, AdaBoost with stumps, gradient-boosted trees for a yes/no label,
impurity and permutation feature importance, and a linear support vector
machine trained by subgradient descent on the hinge loss (plus the
epsilon-insensitive loss for regression).
"""

import pathlib
import sys
from dataclasses import dataclass

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'classical-machine-learning')
PNG_DIR: pathlib.Path | None = None     # set by --png <dir> to also write PNG copies

GRID: str = '#d6d6d6'
LINK: str = '#3b82c4'
LINK_PALE: str = '#c9dcef'
JOINT: str = '#f0a500'
SLIDE: str = '#2a9d3f'
GRIP: str = '#e05555'
GRIP_PALE: str = '#f6cccc'
WRIST: str = '#e07b39'
PURPLE: str = '#6a4fb3'
TEAL: str = '#0f8b8d'
INK: str = '#222222'
MUTED: str = '#777777'

TREE_DOC: str = 'decision-trees-and-forests'
SVM_DOC: str = 'support-vector-machines'

Arr = NDArray[np.float64]
IArr = NDArray[np.int64]


# --------------------------------------------------------------------------
# small helpers
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


def _sigmoid(z: Arr) -> Arr:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -40, 40)))


# --------------------------------------------------------------------------
# decision trees: one tree builder for yes/no labels and for boosting
# --------------------------------------------------------------------------

@dataclass
class Node:
    value: float                 # the answer stored here (share of "yes", or a correction)
    n: int                       # number of training examples that reached this node
    feature: int = -1            # -1 means a leaf
    threshold: float = 0.0
    gain: float = 0.0            # drop in impurity from this split, times the weight
    left: 'Node | None' = None   # feature <= threshold
    right: 'Node | None' = None


def _best_split(x: Arr, y: Arr, w: Arr, features: IArr,
                min_leaf: int) -> tuple[int, float, float]:
    """Return (feature, threshold, weighted impurity after the split).

    The impurity is the weighted sum of squared differences from each side's
    mean. For a 0/1 label that is exactly half the Gini impurity times the
    weight, so the same code serves yes/no trees and boosting trees.
    """
    best = (-1, 0.0, np.inf)
    for f in features:
        order = np.argsort(x[:, f], kind='stable')
        xs, ys, ws = x[order, f], y[order], w[order]
        cw, cs, cq = np.cumsum(ws), np.cumsum(ws * ys), np.cumsum(ws * ys * ys)
        W, S, Q = cw[-1], cs[-1], cq[-1]
        n = len(xs)
        k = np.arange(min_leaf, n - min_leaf + 1)           # left side = first k items
        if len(k) == 0:
            continue
        k = k[xs[k - 1] < xs[np.minimum(k, n - 1)]]         # only between distinct values
        if len(k) == 0:
            continue
        wl, sl, ql = cw[k - 1], cs[k - 1], cq[k - 1]
        wr, sr, qr = W - wl, S - sl, Q - ql
        sse = (ql - sl ** 2 / wl) + (qr - sr ** 2 / wr)
        i = int(np.argmin(sse))
        if sse[i] < best[2] - 1e-12:
            best = (int(f), float(0.5 * (xs[k[i] - 1] + xs[k[i]])), float(sse[i]))
    return best


def grow_tree(x: Arr, y: Arr, w: Arr | None = None, max_depth: int = 99,
              min_leaf: int = 1, max_features: int | None = None,
              rng: np.random.Generator | None = None) -> Node:
    """A CART tree: at each node try every feature and every cut, keep the purest."""
    if w is None:
        w = np.ones(len(y))
    n_feat = x.shape[1]

    def grow(idx: IArr, depth: int) -> Node:
        ww, yy = w[idx], y[idx]
        mean = float(np.sum(ww * yy) / np.sum(ww))
        node = Node(value=mean, n=len(idx))
        sse_here = float(np.sum(ww * (yy - mean) ** 2))
        if depth >= max_depth or len(idx) < 2 * min_leaf or sse_here < 1e-12:
            return node
        if max_features is None or rng is None:
            feats = np.arange(n_feat)
        else:
            feats = rng.choice(n_feat, size=max_features, replace=False)
        f, t, sse = _best_split(x[idx], yy, ww, feats, min_leaf)
        if f < 0:
            return node
        node.feature, node.threshold, node.gain = f, t, sse_here - sse
        go_left = x[idx, f] <= t
        node.left = grow(idx[go_left], depth + 1)
        node.right = grow(idx[~go_left], depth + 1)
        return node

    return grow(np.arange(len(y)), 0)


def tree_predict(node: Node, x: Arr) -> Arr:
    out = np.empty(len(x))

    def walk(nd: Node, idx: IArr) -> None:
        if nd.feature < 0 or nd.left is None or nd.right is None:
            out[idx] = nd.value
            return
        go_left = x[idx, nd.feature] <= nd.threshold
        walk(nd.left, idx[go_left])
        walk(nd.right, idx[~go_left])

    walk(node, np.arange(len(x)))
    return out


def tree_leaves(node: Node) -> list[Node]:
    if node.feature < 0 or node.left is None or node.right is None:
        return [node]
    return tree_leaves(node.left) + tree_leaves(node.right)


def tree_depth(node: Node) -> int:
    if node.feature < 0 or node.left is None or node.right is None:
        return 0
    return 1 + max(tree_depth(node.left), tree_depth(node.right))


def tree_gains(node: Node, n_feat: int) -> Arr:
    g = np.zeros(n_feat)
    if node.feature >= 0 and node.left is not None and node.right is not None:
        g[node.feature] += node.gain
        g += tree_gains(node.left, n_feat) + tree_gains(node.right, n_feat)
    return g


def tree_rules(node: Node, names: list[str], indent: str = '') -> list[str]:
    if node.feature < 0 or node.left is None or node.right is None:
        return [f'{indent}-> slip share {node.value:.2f} ({node.n} examples)']
    nm = names[node.feature]
    return ([f'{indent}if {nm} <= {node.threshold:.3f}:']
            + tree_rules(node.left, names, indent + '    ')
            + [f'{indent}else ({nm} > {node.threshold:.3f}):']
            + tree_rules(node.right, names, indent + '    '))


def _acc(p: Arr, y: Arr) -> float:
    return float(np.mean((p > 0.5) == (y > 0.5)))


# --------------------------------------------------------------------------
# the slip data: two force features, label "slipping" or "holding"
# --------------------------------------------------------------------------

SLIP_NAMES: list[str] = ['sideways ratio', 'shaking']


def _slip_truth(x: Arr) -> Arr:
    """The made-up true rule: slip when pulled hard sideways, or when
    pulled a bit sideways while the force signal shakes."""
    r, v = x[:, 0], x[:, 1]
    return ((r > 0.62) | ((r > 0.38) & (v > 0.55))).astype(float)


def make_slip(n: int, rng: np.random.Generator, flip: float = 0.08) -> tuple[Arr, Arr]:
    x = np.column_stack([rng.uniform(0.0, 1.0, n), rng.uniform(0.0, 1.0, n)])
    y = _slip_truth(x)
    wrong = rng.random(n) < flip
    y[wrong] = 1.0 - y[wrong]
    return x, y


class SlipSet:
    def __init__(self) -> None:
        rng = np.random.default_rng(3)
        self.x, self.y = make_slip(200, rng)
        self.xt, self.yt = make_slip(4000, rng)


SLIP: SlipSet | None = None


def _slip() -> SlipSet:
    global SLIP
    if SLIP is None:
        SLIP = SlipSet()
    return SLIP


def _gini(y: Arr) -> float:
    if len(y) == 0:
        return 0.0
    p = y.mean()
    return float(2 * p * (1 - p))


def _split_curve(x: Arr, y: Arr, f: int, cuts: Arr) -> Arr:
    out = []
    for c in cuts:
        left, right = y[x[:, f] <= c], y[x[:, f] > c]
        out.append((len(left) * _gini(left) + len(right) * _gini(right)) / len(y))
    return np.array(out)


def choosing_a_split() -> None:
    s = _slip()
    x, y = s.x, s.y
    print(f'[split] {len(y)} examples, {int(y.sum())} slip, Gini at the top {_gini(y):.3f}')
    cuts = np.linspace(0.02, 0.98, 97)
    curves = [_split_curve(x, y, f, cuts) for f in (0, 1)]
    f, t, _ = _best_split(x, y, np.ones(len(y)), np.arange(2), 1)
    left, right = y[x[:, f] <= t], y[x[:, f] > t]
    after = (len(left) * _gini(left) + len(right) * _gini(right)) / len(y)
    print(f'[split] best first split: {SLIP_NAMES[f]} <= {t:.3f}; left {len(left)} '
          f'({int(left.sum())} slip, Gini {_gini(left):.3f}), right {len(right)} '
          f'({int(right.sum())} slip, Gini {_gini(right):.3f}); weighted Gini {after:.3f}')
    ib = int(np.argmin(curves[1]))
    print(f'[split] best cut on shaking: {cuts[ib]:.2f} gives {curves[1][ib]:.3f}')
    for c in (0.2, 0.5, 0.8):
        i = int(np.argmin(np.abs(cuts - c)))
        print(f'[split] ratio cut {c}: weighted Gini {curves[0][i]:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1.0, 1.25]})
    ax = axes[0]
    _plain(ax)
    ax.axvspan(0, t, color=LINK_PALE, alpha=0.45, lw=0)
    ax.axvspan(t, 1, color=GRIP_PALE, alpha=0.45, lw=0)
    ax.scatter(x[y == 0, 0], x[y == 0, 1], s=18, color=LINK, label='holding')
    ax.scatter(x[y == 1, 0], x[y == 1, 1], s=18, color=GRIP, marker='^', label='slipping')
    ax.axvline(t, color=INK, lw=1.8)
    ax.text(t / 2, 1.04, f'{len(left)} examples\n{int(left.sum())} slipping',
            ha='center', va='bottom', fontsize=9.5, color=INK)
    ax.text((t + 1) / 2, 1.04, f'{len(right)} examples\n{int(right.sum())} slipping',
            ha='center', va='bottom', fontsize=9.5, color=INK)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('sideways force ÷ squeezing force', fontsize=10)
    ax.set_ylabel('shaking in the force signal (0 to 1)', fontsize=10)
    ax.set_title(f'The best first question: is the ratio above {t:.2f}?',
                 fontsize=11.5, weight='bold', pad=36)
    ax.legend(fontsize=9, frameon=True, loc='lower left', framealpha=0.9)

    ax = axes[1]
    _plain(ax)
    ax.plot(cuts, curves[0], color=WRIST, lw=2.2, label='cut on the sideways ratio')
    ax.plot(cuts, curves[1], color=PURPLE, lw=2.2, label='cut on the shaking')
    ax.axhline(_gini(y), color=MUTED, lw=1.0, ls='--')
    ax.text(0.99, _gini(y) + 0.006, f'before any cut: {_gini(y):.3f}', ha='right',
            va='bottom', fontsize=9, color=MUTED)
    ax.scatter([t], [after], s=60, color=INK, zorder=5)
    ax.annotate(f'lowest: cut at {t:.2f}\nGini {after:.3f}', (t, after),
                xytext=(t - 0.43, after - 0.035), fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle='->', color=INK, lw=1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0.2, 0.52)
    ax.set_xlabel('where the cut is placed', fontsize=10)
    ax.set_ylabel('Gini impurity after the cut\n(lower = purer groups)', fontsize=10)
    ax.set_title('Try every cut on every feature; keep the lowest', fontsize=11.5,
                 weight='bold', pad=36)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    fig.tight_layout()
    _save(fig, TREE_DOC, 'choosing-a-split.svg')


GRID_N: int = 220


def _grid() -> tuple[Arr, Arr, Arr]:
    g = np.linspace(0, 1, GRID_N)
    gx, gy = np.meshgrid(g, g)
    return gx, gy, np.column_stack([gx.ravel(), gy.ravel()])


def _regions(ax: Axes, p: Arr, soft: bool = False) -> None:
    gx, gy, _ = _grid()
    if soft:
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            'b2r', ['#dbe8f5', '#ffffff', '#f7d6d6'])
        ax.pcolormesh(gx, gy, p.reshape(gx.shape), cmap=cmap, vmin=0, vmax=1,
                      shading='auto', rasterized=True)
        ax.contour(gx, gy, p.reshape(gx.shape), levels=[0.5], colors=INK, linewidths=1.3)
    else:
        cmap = ListedColormap(['#dbe8f5', '#f7d6d6'])
        ax.pcolormesh(gx, gy, (p.reshape(gx.shape) > 0.5).astype(float), cmap=cmap,
                      vmin=0, vmax=1, shading='auto', rasterized=True)


def _truth_outline(ax: Axes) -> None:
    ax.plot([0.62, 0.62, 1.0], [0.0, 0.55, 0.55], color=MUTED, lw=0, alpha=0)  # keep limits
    ax.plot([0.62, 0.62], [0.0, 0.55], color=INK, lw=1.0, ls=':')
    ax.plot([0.38, 0.62], [0.55, 0.55], color=INK, lw=1.0, ls=':')
    ax.plot([0.38, 0.38], [0.55, 1.0], color=INK, lw=1.0, ls=':')


def _slip_points(ax: Axes, x: Arr, y: Arr, s: float = 12) -> None:
    ax.scatter(x[y == 0, 0], x[y == 0, 1], s=s, color=LINK, lw=0)
    ax.scatter(x[y == 1, 0], x[y == 1, 1], s=s, color=GRIP, marker='^', lw=0)


def depth_and_overfitting() -> None:
    s = _slip()
    depths = list(range(1, 13))
    tr, te = [], []
    for d in depths:
        t = grow_tree(s.x, s.y, max_depth=d)
        tr.append(_acc(tree_predict(t, s.x), s.y))
        te.append(_acc(tree_predict(t, s.xt), s.yt))
    full = grow_tree(s.x, s.y)
    full_tr = _acc(tree_predict(full, s.x), s.y)
    full_te = _acc(tree_predict(full, s.xt), s.yt)
    print('[depth] depth: train / test accuracy')
    for d, a, b in zip(depths, tr, te):
        print(f'[depth]   {d:2d}: {a:.3f} / {b:.3f}')
    print(f'[depth] full tree: depth {tree_depth(full)}, {len(tree_leaves(full))} leaves, '
          f'train {full_tr:.3f}, test {full_te:.3f}')
    best_rule = _acc(_slip_truth(s.xt), s.yt)
    print(f'[depth] the true rule itself scores {best_rule:.3f} on the test set (label noise)')
    t3 = grow_tree(s.x, s.y, max_depth=3)
    print(f'[depth] depth-3 tree: {len(tree_leaves(t3))} leaves')
    for line in tree_rules(t3, SLIP_NAMES):
        print('[depth]   ' + line)
    _, _, g = _grid()

    fig, axes = plt.subplots(1, 3, figsize=(15.2, 5.0), facecolor='white',
                             gridspec_kw={'width_ratios': [1, 1, 1.15]})
    for ax, tree, title, a, b in ((axes[0], t3, f'Depth 3: {len(tree_leaves(t3))} boxes', te[2], tr[2]),
                                  (axes[1], full, f'No depth limit: {len(tree_leaves(full))} boxes',
                                   full_te, full_tr)):
        _plain(ax)
        _regions(ax, tree_predict(tree, g))
        _slip_points(ax, s.x, s.y)
        _truth_outline(ax)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.set_xlabel('sideways force ÷ squeezing force', fontsize=10)
        ax.set_title(f'{title}\ntraining {b:.0%} right, new data {a:.0%} right',
                     fontsize=11, weight='bold')
    axes[0].set_ylabel('shaking in the force signal', fontsize=10)
    axes[0].text(0.02, 0.02, 'dotted line: the true rule', fontsize=8.5, color=INK,
                 bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1.5))

    ax = axes[2]
    _plain(ax)
    ax.plot(depths, np.array(tr) * 100, color=MUTED, lw=2, marker='o', ms=4,
            label='on the 200 training examples')
    ax.plot(depths, np.array(te) * 100, color=LINK, lw=2.4, marker='o', ms=4,
            label='on 4,000 new examples')
    ax.axhline(best_rule * 100, color=SLIDE, lw=1.0, ls='--')
    ax.text(12, best_rule * 100 + 0.4, 'the true rule (labels are noisy)', ha='right',
            va='bottom', fontsize=9, color=SLIDE)
    ax.set_xticks(depths)
    ax.set_ylim(68, 101)
    ax.set_xlabel('largest number of questions (depth)', fontsize=10)
    ax.set_ylabel('share classified right (%)', fontsize=10)
    ax.set_title('Deeper fits the training data;\nnew data peaks, then drops', fontsize=11,
                 weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    fig.tight_layout()
    _save(fig, TREE_DOC, 'depth-and-overfitting.svg')


def grow_forest(x: Arr, y: Arr, n_trees: int, rng: np.random.Generator,
                max_features: int = 1, min_leaf: int = 3) -> list[Node]:
    forest = []
    for _ in range(n_trees):
        idx = rng.integers(0, len(y), len(y))            # draw with replacement
        forest.append(grow_tree(x[idx], y[idx], min_leaf=min_leaf,
                                max_features=max_features, rng=rng))
    return forest


def forest_votes() -> None:
    s = _slip()
    rng = np.random.default_rng(11)
    forest = grow_forest(s.x, s.y, 200, rng)
    votes_t = np.array([(tree_predict(t, s.xt) > 0.5).astype(float) for t in forest])
    counts = [1, 2, 5, 10, 20, 50, 100, 200]
    accs = [_acc(votes_t[:k].mean(axis=0), s.yt) for k in counts]
    for k, a in zip(counts, accs):
        print(f'[forest] {k:3d} trees: test accuracy {a:.3f}')
    single = [_acc(votes_t[i], s.yt) for i in range(len(forest))]
    print(f'[forest] single deep trees on resampled data: mean {np.mean(single):.3f}, '
          f'range {min(single):.3f} to {max(single):.3f}')
    full = grow_tree(s.x, s.y)
    full_te = _acc(tree_predict(full, s.xt), s.yt)
    t3 = grow_tree(s.x, s.y, max_depth=3)
    t3_te = _acc(tree_predict(t3, s.xt), s.yt)
    q = np.array([[0.5, 0.7], [0.5, 0.3], [0.7, 0.2]])
    vq = np.array([(tree_predict(t, q) > 0.5) for t in forest]).mean(axis=0)
    for qq, v in zip(q, vq):
        print(f'[forest] point ratio {qq[0]}, shaking {qq[1]}: {v:.0%} of 200 trees say slip')
    _, _, g = _grid()
    vg = np.mean([(tree_predict(t, g) > 0.5) for t in forest], axis=0)

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.2), facecolor='white',
                             gridspec_kw={'width_ratios': [1, 1.2]})
    ax = axes[0]
    _plain(ax)
    _regions(ax, vg, soft=True)
    _slip_points(ax, s.x, s.y)
    _truth_outline(ax)
    for qq, v in zip(q, vq):
        ax.scatter([qq[0]], [qq[1]], s=110, facecolor='white', edgecolor=INK, lw=1.6, zorder=6)
        ax.text(qq[0] + 0.035, qq[1], f'{v:.0%} say slip', fontsize=9, va='center', zorder=7,
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.set_xlabel('sideways force ÷ squeezing force', fontsize=10)
    ax.set_ylabel('shaking in the force signal', fontsize=10)
    ax.set_title('200 trees vote: colour = share saying "slip"\nblack line = half the votes',
                 fontsize=11, weight='bold')

    ax = axes[1]
    _plain(ax)
    ax.plot(counts, np.array(accs) * 100, color=SLIDE, lw=2.4, marker='o', ms=5,
            label='random forest (majority vote)')
    ax.axhline(full_te * 100, color=GRIP, lw=1.4, ls='--')
    ax.text(200, full_te * 100 - 0.5, f'one deep tree on all the data: {full_te:.0%}',
            ha='right', va='top', fontsize=9, color=GRIP)
    ax.axhline(t3_te * 100, color=LINK, lw=1.4, ls='--')
    ax.text(200, t3_te * 100 + 0.4, f'the best single tree (depth 3): {t3_te:.0%}',
            ha='right', va='bottom', fontsize=9, color=LINK)
    ax.set_xscale('log')
    ax.set_xticks(counts)
    ax.set_xticklabels([str(c) for c in counts])
    ax.set_ylim(78, 93)
    ax.set_xlabel('number of trees in the forest (log scale)', fontsize=10)
    ax.set_ylabel('share of 4,000 new examples right (%)', fontsize=10)
    ax.set_title('More trees: the vote settles close to the best single tree,\n'
                 'with no depth to choose', fontsize=11, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    fig.tight_layout()
    _save(fig, TREE_DOC, 'forest-votes.svg')


# --------------------------------------------------------------------------
# boosting: AdaBoost weights on the slip data, gradient boosting on grasps
# --------------------------------------------------------------------------

def adaboost_weights() -> None:
    """Printed only: how one round of AdaBoost changes the sample weights."""
    s = _slip()
    n = len(s.y)
    w = np.ones(n) / n
    ypm = 2 * s.y - 1
    for rnd in range(1, 4):
        stump = grow_tree(s.x, s.y, w=w, max_depth=1)
        pred = 2 * (tree_predict(stump, s.x) > 0.5) - 1
        wrong = pred != ypm
        err = float(np.sum(w[wrong]))
        alpha = 0.5 * np.log((1 - err) / err)
        before_r, before_w = w[~wrong].mean(), w[wrong].mean()
        w = w * np.exp(-alpha * ypm * pred)
        w = w / w.sum()
        print(f'[ada] round {rnd}: stump on {SLIP_NAMES[stump.feature]} <= '
              f'{stump.threshold:.3f}; {int(wrong.sum())} wrong, weighted error {err:.3f}, '
              f'say {alpha:.2f}; right weight {before_r:.4f}->{w[~wrong].mean():.4f}, '
              f'wrong weight {before_w:.4f}->{w[wrong].mean():.4f}; '
              f'wrong ones now hold {w[wrong].sum():.0%} of the weight')


GRASP_NAMES: list[str] = ['object weight', 'width vs opening', 'grip force', 'friction',
                          'approach angle', 'room temperature']


def _grasp_logit(x: Arr) -> Arr:
    weight, width, force, mu, angle = x[:, 0], x[:, 1], x[:, 2], x[:, 3], x[:, 4]
    margin = 2 * mu * force / (weight * 9.81)            # holding force / weight
    return (2.5 * np.log(margin) - 6.0 * np.maximum(0, width - 0.85) / 0.15
            - 0.15 * np.maximum(0, angle - 30))


def make_grasps(n: int, rng: np.random.Generator) -> tuple[Arr, Arr]:
    x = np.column_stack([rng.uniform(0.05, 1.5, n), rng.uniform(0.2, 1.0, n),
                         rng.uniform(5, 40, n), rng.uniform(0.2, 1.0, n),
                         rng.uniform(0, 45, n), rng.uniform(18, 30, n)])
    y = (rng.random(n) < _sigmoid(_grasp_logit(x))).astype(float)
    return x, y


def boost_fit(x: Arr, y: Arr, n_trees: int, rate: float, depth: int = 3,
              xt: Arr | None = None) -> tuple[float, list[Node], list[Arr]]:
    """Gradient boosting for a yes/no label, on the log-odds scale."""
    p0 = float(np.clip(y.mean(), 1e-6, 1 - 1e-6))
    f0 = float(np.log(p0 / (1 - p0)))
    f = np.full(len(y), f0)
    ft = None if xt is None else np.full(len(xt), f0)
    trees, history = [], []
    for _ in range(n_trees):
        p = _sigmoid(f)
        resid = y - p                                     # what is still wrong
        tree = grow_tree(x, resid, max_depth=depth, min_leaf=5)
        for leaf in tree_leaves(tree):                    # one Newton step per leaf
            leaf.value = 0.0
        _set_newton(tree, x, resid, p * (1 - p))
        trees.append(tree)
        f = f + rate * tree_predict(tree, x)
        if ft is not None and xt is not None:
            ft = ft + rate * tree_predict(tree, xt)
            history.append(ft.copy())
    return f0, trees, history


def _set_newton(node: Node, x: Arr, g: Arr, h: Arr) -> None:
    """Set each leaf to sum(residual) / sum(p(1-p)) over the examples that land there."""
    def walk(nd: Node, idx: IArr) -> None:
        if nd.feature < 0 or nd.left is None or nd.right is None:
            nd.value = float(np.sum(g[idx]) / (np.sum(h[idx]) + 1e-9))
            return
        go_left = x[idx, nd.feature] <= nd.threshold
        walk(nd.left, idx[go_left])
        walk(nd.right, idx[~go_left])
    walk(node, np.arange(len(x)))


def _logloss(f: Arr, y: Arr) -> float:
    p = np.clip(_sigmoid(f), 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def boost_predict(model: tuple[float, list[Node], list[Arr]], x: Arr, rate: float) -> Arr:
    f0, trees, _ = model
    f = np.full(len(x), f0)
    for t in trees:
        f = f + rate * tree_predict(t, x)
    return f


def boosting_on_grasps() -> None:
    rng = np.random.default_rng(21)
    x, y = make_grasps(600, rng)
    xt, yt = make_grasps(4000, rng)
    print(f'[grasp] training: {len(y)} grasps, {y.mean():.0%} succeeded')
    true_ll = _logloss(_grasp_logit(xt), yt)
    true_acc = _acc(_sigmoid(_grasp_logit(xt)), yt)
    print(f'[grasp] the true chances score log loss {true_ll:.3f}, accuracy {true_acc:.3f}')
    base_ll = _logloss(np.full(len(yt), np.log(y.mean() / (1 - y.mean()))), yt)
    print(f'[grasp] a flat guess scores log loss {base_ll:.3f}')
    n_trees = 300
    rates = [(1.0, GRIP), (0.3, JOINT), (0.1, SLIDE)]
    curves = {}
    models = {}
    for r, _c in rates:
        m = boost_fit(x, y, n_trees, r, xt=xt)
        models[r] = m
        curves[r] = np.array([_logloss(f, yt) for f in m[2]])
        best = int(np.argmin(curves[r]))
        acc300 = _acc(_sigmoid(m[2][-1]), yt)
        accbest = _acc(_sigmoid(m[2][best]), yt)
        print(f'[grasp] rate {r}: best log loss {curves[r][best]:.3f} at {best + 1} trees '
              f'(accuracy {accbest:.3f}); after {n_trees}: {curves[r][-1]:.3f} '
              f'(accuracy {acc300:.3f}); after 10: {curves[r][9]:.3f}')

    # feature importance of the rate-0.1 model
    m = models[0.1]
    imp = np.sum([tree_gains(t, x.shape[1]) for t in m[1]], axis=0)
    imp = imp / imp.sum()
    f_base = boost_predict(m, xt, 0.1)
    ll0 = _logloss(f_base, yt)
    perm = np.zeros(x.shape[1])
    prng = np.random.default_rng(5)
    for j in range(x.shape[1]):
        drops = []
        for _ in range(5):
            xp = xt.copy()
            xp[:, j] = prng.permutation(xp[:, j])
            drops.append(_logloss(boost_predict(m, xp, 0.1), yt) - ll0)
        perm[j] = np.mean(drops)
    for j, nm in enumerate(GRASP_NAMES):
        print(f'[grasp] importance {nm:17s}: split gain {imp[j]:.3f}, '
              f'shuffle raises log loss by {perm[j]:.3f}')

    # ranking candidate grasps on one mug
    cands = np.array([
        [0.35, 0.55, 12, 0.5, 5, 22],
        [0.35, 0.55, 25, 0.5, 5, 22],
        [0.35, 0.95, 25, 0.5, 5, 22],
        [0.35, 0.55, 25, 0.5, 40, 22],
        [0.35, 0.40, 35, 0.5, 15, 22],
        [0.35, 0.55, 6, 0.5, 5, 22],
    ])
    pc = _sigmoid(boost_predict(m, cands, 0.1))
    pt = _sigmoid(_grasp_logit(cands))
    order = np.argsort(-pc)
    print('[grasp] candidates ranked (width, force, angle, predicted, true):')
    for i in order:
        c = cands[i]
        print(f'[grasp]   #{i + 1}: width {c[1]:.2f}, force {c[2]:.0f} N, angle {c[4]:.0f} deg '
              f'-> {pc[i]:.2f} (true {pt[i]:.2f})')

    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.2), facecolor='white',
                             gridspec_kw={'width_ratios': [1.25, 1]})
    ax = axes[0]
    _plain(ax)
    k = np.arange(1, n_trees + 1)
    for r, c in rates:
        best = int(np.argmin(curves[r]))
        ax.plot(k, curves[r], color=c, lw=2.2, label=f'learning rate {r}')
        ax.scatter([best + 1], [curves[r][best]], color=c, s=40, zorder=5,
                   edgecolor='white')
    ax.axhline(true_ll, color=MUTED, lw=1.0, ls='--')
    ax.text(n_trees, true_ll - 0.004, 'the true chances (best possible)', ha='right',
            va='top', fontsize=9, color=MUTED)
    ax.set_xlim(0, n_trees)
    ax.set_ylim(true_ll - 0.04, 0.62)
    ax.set_xlabel('number of trees added', fontsize=10)
    ax.set_ylabel('error on 4,000 new grasps\n(log loss, lower is better)', fontsize=10)
    ax.set_title('A small learning rate learns slower, and ends better\n(dot = lowest point)',
                 fontsize=11, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')

    ax = axes[1]
    _plain(ax)
    yy = np.arange(len(GRASP_NAMES))[::-1]
    ax.barh(yy + 0.19, imp, height=0.36, color=LINK, label='share of split gain')
    ax.barh(yy - 0.19, perm / perm.max() * imp.max(), height=0.36, color=WRIST,
            label='rise in error when shuffled\n(scaled to the same longest bar)')
    ax.set_yticks(yy)
    ax.set_yticklabels(GRASP_NAMES, fontsize=10)
    ax.set_xlabel('importance', fontsize=10)
    ax.set_title('Which columns the trees used', fontsize=11, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='lower right')
    fig.tight_layout()
    _save(fig, TREE_DOC, 'boosting-on-grasps.svg')


# --------------------------------------------------------------------------
# support vector machines, trained by subgradient descent
# --------------------------------------------------------------------------

def svm_fit(x: Arr, y: Arr, lam: float, steps: int = 40000) -> tuple[Arr, float]:
    """Linear SVM: minimise lam/2 |w|^2 + mean(max(0, 1 - y (w.x + b))), y in {-1, +1}.

    Full-batch subgradient descent with the step 1 / (lam t), which shrinks as
    training goes on (the Pegasos schedule). The answer is the average of the
    second half of the steps, which removes the zig-zag of the last few steps.
    """
    n, d = x.shape
    w, b = np.zeros(d), 0.0
    w_sum, b_sum, count = np.zeros(d), 0.0, 0
    for t in range(1, steps + 1):
        act = y * (x @ w + b) < 1                          # inside the gap, or wrong
        gw = lam * w - (y[act, None] * x[act]).sum(axis=0) / n
        gb = -y[act].sum() / n
        step = 1.0 / (lam * t)
        w, b = w - step * gw, b - step * gb
        if t > steps // 2:
            w_sum, b_sum, count = w_sum + w, b_sum + b, count + 1
    return w_sum / count, b_sum / count


def svr_fit(x: Arr, y: Arr, lam: float, eps: float, steps: int = 40000,
            lr0: float = 0.5) -> tuple[Arr, float]:
    """Linear support vector regression with the epsilon-insensitive loss."""
    n, d = x.shape
    w, b = np.zeros(d), float(np.median(y))
    best = (np.inf, w.copy(), b)
    for t in range(1, steps + 1):
        r = x @ w + b - y
        out = np.abs(r) > eps
        s = np.sign(r) * out
        gw = lam * w + (s[:, None] * x).sum(axis=0) / n
        gb = s.sum() / n
        step = lr0 / np.sqrt(t)
        w, b = w - step * gw, b - step * gb
        obj = 0.5 * lam * w @ w + np.mean(np.maximum(0, np.abs(x @ w + b - y) - eps))
        if obj < best[0]:
            best = (obj, w.copy(), b)
    return best[1], best[2]


def _contact_data(n: int, rng: np.random.Generator, spread: float) -> tuple[Arr, Arr]:
    """Two features from the wrist, both scaled to about 0..1: the jump in
    force, and the gap between expected and measured joint torque.
    Contact (+1) points sit up and to the right of free motion (-1)."""
    y = np.where(rng.random(n) < 0.5, 1.0, -1.0)
    centre = np.where(y[:, None] > 0, np.array([0.66, 0.62]), np.array([0.32, 0.30]))
    x = centre + rng.normal(0, spread, (n, 2))
    return x, y


def _line(ax: Axes, w: Arr, b: float, level: float, **kw: object) -> None:
    xs = np.array([-0.2, 1.2])
    if abs(w[1]) > 1e-9:
        ax.plot(xs, (level - b - w[0] * xs) / w[1], **kw)  # type: ignore[arg-type]


def widest_gap() -> None:
    rng = np.random.default_rng(5)
    x, y = _contact_data(40, rng, 0.07)
    w, b = svm_fit(x, y, lam=1e-4, steps=100000)
    m = y * (x @ w + b)
    sv = m <= 1.01
    width = 2 / np.linalg.norm(w)
    print(f'[gap] 40 examples; min margin value {m.min():.3f}; all right: {bool((m > 0).all())}')
    print(f'[gap] gap width {width:.3f}; support vectors {int(sv.sum())}: '
          + ', '.join(f'({x[i, 0]:.2f},{x[i, 1]:.2f}) y={int(y[i])} m={m[i]:.2f}'
                      for i in np.where(sv)[0]))
    # three other lines that also separate every example
    others = [(np.array([1.0, 0.25]), -0.62), (np.array([0.35, 1.0]), -0.68),
              (np.array([1.0, 1.0]), -0.93)]
    for ow, ob in others:
        s = y * (x @ ow + ob)
        gap = 2 * np.min(np.abs(x @ ow + ob)) / np.linalg.norm(ow)
        print(f'[gap] other line {ow}, {ob}: separates all {bool((s > 0).all())}, '
              f'gap {gap:.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.6), facecolor='white')
    for ax in axes:
        _plain(ax)
        ax.scatter(x[y < 0, 0], x[y < 0, 1], s=26, color=LINK, label='moving freely')
        ax.scatter(x[y > 0, 0], x[y > 0, 1], s=30, color=GRIP, marker='^', label='touching')
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        ax.set_aspect('equal')
        ax.set_xlabel('jump in wrist force (scaled)', fontsize=10)
    axes[0].set_ylabel('torque the arm did not expect (scaled)', fontsize=10)
    ax = axes[0]
    for (ow, ob), c in zip(others, (JOINT, PURPLE, TEAL)):
        gap = 2 * np.min(np.abs(x @ ow + ob)) / np.linalg.norm(ow)
        _line(ax, ow, ob, 0.0, color=c, lw=1.8, label=f'a line with a gap of {gap:.2f}')
    ax.set_title('Many lines split the two groups', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=True, framealpha=0.9, loc='upper left')
    ax = axes[1]
    gx, gy, g = _grid()
    f = (g @ w + b).reshape(gx.shape)
    ax.contourf(gx, gy, np.abs(f) < 1, levels=[0.5, 1.5], colors=['#eeeeee'])
    _line(ax, w, b, 0.0, color=INK, lw=2.2)
    _line(ax, w, b, 1.0, color=INK, lw=1.0, ls='--')
    _line(ax, w, b, -1.0, color=INK, lw=1.0, ls='--')
    ax.scatter(x[sv, 0], x[sv, 1], s=170, facecolor='none', edgecolor=INK, lw=1.5, zorder=6)
    ax.set_title('The support vector machine picks the widest gap', fontsize=11.5,
                 weight='bold')
    ax.text(0.98, 0.03, f'gap {width:.2f}, the widest possible\n'
            f'the {int(sv.sum())} circled points touch its edges:\nthey are the support vectors', ha='right', va='bottom', fontsize=9.5,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.9, pad=2))
    fig.tight_layout()
    _save(fig, SVM_DOC, 'widest-gap.svg')


def soft_margin() -> None:
    rng = np.random.default_rng(10)
    x, y = _contact_data(80, rng, 0.14)
    xt, yt = _contact_data(4000, rng, 0.14)
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.6), facecolor='white')
    gx, gy, g = _grid()
    for ax, lam in zip(axes, (0.03, 1e-4)):
        w, b = svm_fit(x, y, lam=lam, steps=40000)
        m = y * (x @ w + b)
        sv = m <= 1.001
        inside = (m < 1) & (m > 0)
        wrong = m <= 0
        acc = float(np.mean(np.sign(xt @ w + b) == yt))
        c_val = 1 / (lam * len(y))
        width = 2 / np.linalg.norm(w)
        print(f'[soft] lambda {lam} (C = {c_val:.3g}): gap width {width:.3f}; support vectors '
              f'{int(sv.sum())}; inside gap {int(inside.sum())}; wrong side {int(wrong.sum())}; '
              f'test accuracy {acc:.3f}')
        _plain(ax)
        f = (g @ w + b).reshape(gx.shape)
        ax.contourf(gx, gy, np.abs(f) < 1, levels=[0.5, 1.5], colors=['#eeeeee'])
        ax.scatter(x[y < 0, 0], x[y < 0, 1], s=22, color=LINK, label='moving freely')
        ax.scatter(x[y > 0, 0], x[y > 0, 1], s=26, color=GRIP, marker='^', label='touching')
        ax.scatter(x[sv, 0], x[sv, 1], s=120, facecolor='none', edgecolor=INK, lw=1.1, zorder=6)
        _line(ax, w, b, 0.0, color=INK, lw=2.2)
        _line(ax, w, b, 1.0, color=INK, lw=1.0, ls='--')
        _line(ax, w, b, -1.0, color=INK, lw=1.0, ls='--')
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        ax.set_aspect('equal')
        ax.set_xlabel('jump in wrist force (scaled)', fontsize=10)
        soft_word = 'Soft gap: small C' if lam > 0.01 else 'Strict gap: large C'
        ax.set_title(f'{soft_word} (C = {c_val:.3g})\n{int(sv.sum())} support vectors, '
                     f'{acc:.1%} right on new data', fontsize=11, weight='bold')
    axes[0].set_ylabel('torque the arm did not expect (scaled)', fontsize=10)
    axes[0].legend(fontsize=9, frameon=True, framealpha=0.9, loc='upper left')
    fig.tight_layout()
    _save(fig, SVM_DOC, 'soft-margin.svg')


def kernel_trick() -> None:
    rng = np.random.default_rng(6)
    n = 160
    off = rng.uniform(-20, 20, (n, 2))                      # gripper offset from centre, mm
    r2 = (off ** 2).sum(axis=1)
    y = np.where(r2 < 11.0 ** 2, 1.0, -1.0)
    flip = rng.random(n) < 0.04
    y[flip] = -y[flip]
    offt = rng.uniform(-20, 20, (4000, 2))
    yt = np.where((offt ** 2).sum(axis=1) < 11.0 ** 2, 1.0, -1.0)
    print(f'[kernel] {n} grasps, {int((y > 0).sum())} succeeded')

    s = 20.0
    w1, b1 = svm_fit(off / s, y, lam=0.01)
    acc1 = float(np.mean(np.sign(offt / s @ w1 + b1) == yt))
    print(f'[kernel] straight line in (x, y): test accuracy {acc1:.3f}; '
          f'share of failures in test set {np.mean(yt < 0):.3f}')

    def lift(o: Arr) -> Arr:
        return np.column_stack([o[:, 0] / s, o[:, 1] / s, (o ** 2).sum(axis=1) / s ** 2])
    w2, b2 = svm_fit(lift(off), y, lam=0.01)
    acc2 = float(np.mean(np.sign(lift(offt) @ w2 + b2) == yt))
    radius = np.sqrt(max(-b2 / w2[2], 0)) * s
    print(f'[kernel] with the extra column x^2 + y^2: w = {np.round(w2, 2)}, b = {b2:.2f}; '
          f'test accuracy {acc2:.3f}; flat cut at distance^2 = {-b2 / w2[2] * s ** 2:.1f} '
          f'(about {radius:.1f} mm)')

    fig, axes = plt.subplots(1, 3, figsize=(15.6, 5.2), facecolor='white')
    for ax in (axes[0], axes[2]):
        _plain(ax)
        ax.scatter(off[y < 0, 0], off[y < 0, 1], s=16, color=LINK, label='grasp failed')
        ax.scatter(off[y > 0, 0], off[y > 0, 1], s=20, color=GRIP, marker='^',
                   label='grasp held')
        ax.set_xlim(-20, 20)
        ax.set_ylim(-20, 20)
        ax.set_aspect('equal')
        ax.set_xlabel('gripper offset left-right (mm)', fontsize=10)
        ax.set_ylabel('gripper offset front-back (mm)', fontsize=10)
    ax = axes[0]
    xs = np.array([-25, 25])
    if abs(w1[1]) > 1e-6:
        ax.plot(xs, (-b1 - w1[0] * xs / s) / w1[1] * s, color=INK, lw=2)
    ax.set_title(f'1. The best straight line gives up:\nit says "failed" every time ({acc1:.0%} right)',
                 fontsize=11, weight='bold')
    ax.legend(fontsize=8.5, frameon=True, framealpha=0.9, loc='upper left')

    ax = axes[1]
    _plain(ax)
    d2 = (off ** 2).sum(axis=1)
    ax.scatter(off[y < 0, 0], d2[y < 0], s=16, color=LINK)
    ax.scatter(off[y > 0, 0], d2[y > 0], s=20, color=GRIP, marker='^')
    xx = np.linspace(-20, 20, 50)
    ax.plot(xx, -(b2 + w2[0] * xx / s) / w2[2] * s ** 2, color=INK, lw=2)  # front-back term ~0
    ax.set_xlim(-20, 20)
    ax.set_xlabel('gripper offset left-right (mm)', fontsize=10)
    ax.set_ylabel('new column: left-right² + front-back² (mm²)', fontsize=10)
    ax.set_title('2. Add a column: distance² from the centre\nnow a straight cut splits them',
                 fontsize=11, weight='bold')

    ax = axes[2]
    gg = np.linspace(-20, 20, 300)
    gx, gy = np.meshgrid(gg, gg)
    gp = np.column_stack([gx.ravel(), gy.ravel()])
    f = (lift(gp) @ w2 + b2).reshape(gx.shape)
    ax.contour(gx, gy, f, levels=[0], colors=INK, linewidths=2)
    ax.set_title(f'3. Back in the first picture, the cut is a circle\n{acc2:.0%} right '
                 'on new data', fontsize=11, weight='bold')
    fig.tight_layout()
    _save(fig, SVM_DOC, 'kernel-trick.svg')


def svm_regression() -> None:
    rng = np.random.default_rng(12)
    n = 30
    temp = rng.uniform(18, 38, n)                          # sensor temperature, deg C
    drift = 0.09 * (temp - 18) + rng.normal(0, 0.12, n)    # force offset, N
    drift[[3, 17]] += np.array([1.6, 1.3])                  # two readings hit by a knock
    xs = ((temp - 18) / 20)[:, None]
    eps = 0.2
    w, b = svr_fit(xs, drift, lam=1e-3, eps=eps, steps=60000)
    slope = w[0] / 20
    res = drift - (xs @ w + b)
    outside = np.abs(res) > eps + 1e-3
    a = np.column_stack([np.ones(n), temp])
    ls_coef = np.linalg.lstsq(a, drift, rcond=None)[0]
    print(f'[svr] true slope 0.090 N per deg; SVR slope {slope:.3f}, least squares '
          f'{ls_coef[1]:.3f}; SVR at 18 C {b:.3f}, least squares {ls_coef[0] + 18 * ls_coef[1]:.3f}; '
          f'{int(outside.sum())} of {n} points outside the tube of +-{eps} N')

    fig, ax = plt.subplots(figsize=(8.4, 5.0), facecolor='white')
    _plain(ax)
    tt = np.linspace(17, 39, 100)
    ft = w[0] * (tt - 18) / 20 + b
    ax.fill_between(tt, ft - eps, ft + eps, color=LINK_PALE, alpha=0.7, lw=0,
                    label=f'the tube: ±{eps} N, errors inside cost nothing')
    ax.plot(tt, ft, color=LINK, lw=2.2, label=f'SVM for regression: {slope:.3f} N per °C')
    ax.plot(tt, ls_coef[0] + ls_coef[1] * tt, color=WRIST, lw=1.6, ls='--',
            label=f'least squares: {ls_coef[1]:.3f} N per °C')
    ax.scatter(temp[~outside], drift[~outside], s=22, color=INK, zorder=5)
    ax.scatter(temp[outside], drift[outside], s=60, facecolor='white', edgecolor=GRIP,
               lw=1.8, zorder=6, label='outside the tube: only these, and the points\non its edge, decide where the line goes')
    ax.set_xlim(17, 39)
    ax.set_xlabel('force sensor temperature (°C)', fontsize=10)
    ax.set_ylabel('reading with nothing attached (N)', fontsize=10)
    ax.set_title(f'Fit a tube: errors smaller than {eps} N cost nothing\n'
                 'the true drift is 0.090 N per °C', fontsize=11.5, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    fig.tight_layout()
    _save(fig, SVM_DOC, 'svm-regression.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    choosing_a_split()
    depth_and_overfitting()
    forest_votes()
    adaboost_weights()
    boosting_on_grasps()
    widest_gap()
    soft_margin()
    kernel_trick()
    svm_regression()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
