"""Generate the diagrams for two pages of docs/07_learned-models/01_what-models-are/.

    06_uncertainty-and-confidence.md   -> images/what-models-are/uncertainty-and-confidence/
    08_classical-machine-learning.md   -> images/what-models-are/classical-machine-learning/

Run with:  pixi run python ../docs/diagrams/what_models_are_3.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is computed in this file, and the script prints
them so the documents can quote the same values. The data is simulated: the
scores come from a made-up five-class "model" whose true answers are drawn at
random, and the depth-camera errors come from a made-up formula plus noise.
The methods run on that data are real (temperature scaling, a reliability
curve, a small ensemble of networks, dropout at prediction time, split
conformal prediction, ridge regression, a Gaussian process, gradient-boosted
trees, k-nearest neighbours and a small neural network), written in NumPy.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'what-models-are'
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

UNC_DOC: str = 'uncertainty-and-confidence'
CML_DOC: str = 'classical-machine-learning'

Arr = NDArray[np.float64]


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


def _softmax(z: Arr) -> Arr:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


# --------------------------------------------------------------------------
# 06_uncertainty-and-confidence: the simulated five-class model
# --------------------------------------------------------------------------

CLASSES: list[str] = ['mug', 'cup', 'bowl', 'jar', 'box']


def _simulate(n: int, rng: np.random.Generator) -> tuple[Arr, NDArray[np.int64]]:
    """Return a model's raw outputs (logits) and the true labels for n pictures.

    The 'honest' logits give the true chance of each class. The model's logits
    are those multiplied by 2.5, which makes it overconfident, as trained
    networks often are.
    """
    honest = rng.normal(0.0, 0.8, size=(n, 5))
    favourite = rng.integers(0, 5, size=n)
    honest[np.arange(n), favourite] += rng.uniform(1.5, 6.0, size=n)
    p_true = _softmax(honest)
    labels = np.array([rng.choice(5, p=p) for p in p_true])
    return honest * 2.5, labels


def _bins(conf: Arr, correct: Arr, n_bins: int = 10) -> tuple[Arr, Arr, Arr, float]:
    """Reliability curve: mean confidence, accuracy and count per bin, plus the ECE."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    mc, acc, cnt = np.zeros(n_bins), np.zeros(n_bins), np.zeros(n_bins)
    for b in range(n_bins):
        m = (conf > edges[b]) & (conf <= edges[b + 1])
        cnt[b] = m.sum()
        if cnt[b] > 0:
            mc[b] = conf[m].mean()
            acc[b] = correct[m].mean()
    ece = float(np.sum(cnt / len(conf) * np.abs(acc - mc)))
    return mc, acc, cnt, ece


def _nll(logits: Arr, labels: NDArray[np.int64], t: float) -> float:
    p = _softmax(logits / t)
    return float(-np.mean(np.log(p[np.arange(len(labels)), labels] + 1e-12)))


class Sim:
    """All the simulated numbers used by the uncertainty page, computed once."""

    def __init__(self) -> None:
        rng = np.random.default_rng(6)
        self.val_logits, self.val_labels = _simulate(2000, rng)
        self.test_logits, self.test_labels = _simulate(2000, rng)
        ts = np.arange(0.5, 5.001, 0.01)
        nlls = [_nll(self.val_logits[:1000], self.val_labels[:1000], t) for t in ts]
        self.t = float(ts[int(np.argmin(nlls))])
        self.p_before = _softmax(self.test_logits)
        self.p_after = _softmax(self.test_logits / self.t)
        pred = self.p_before.argmax(1)
        self.correct = (pred == self.test_labels).astype(float)
        self.accuracy = float(self.correct.mean())
        self.acc_after = float((self.p_after.argmax(1) == self.test_labels).mean())
        self.conf_before = self.p_before.max(1)
        self.conf_after = self.p_after.max(1)
        self.rel_before = _bins(self.conf_before, self.correct)
        self.rel_after = _bins(self.conf_after, self.correct)


SIM: Sim | None = None


def _sim() -> Sim:
    global SIM
    if SIM is None:
        SIM = Sim()
    return SIM


def reliability_curve() -> None:
    s = _sim()
    print(f'[calib] accuracy {s.accuracy:.3f} (after scaling {s.acc_after:.3f}), '
          f'mean conf before {s.conf_before.mean():.3f}, after {s.conf_after.mean():.3f}')
    print(f'[calib] fitted temperature T = {s.t:.2f}')
    print(f'[calib] ECE before {s.rel_before[3]:.3f}, after {s.rel_after[3]:.3f}')
    for name, rel in (('before', s.rel_before), ('after', s.rel_after)):
        mc, acc, cnt, _ = rel
        rows = [f'{m:.2f}->{a:.2f} (n={int(c)})' for m, a, c in zip(mc, acc, cnt) if c > 0]
        print(f'[calib] bins {name}: ' + '; '.join(rows))
    hi = s.conf_before > 0.9
    print(f'[calib] before: {hi.sum()} pictures above 0.9, right on '
          f'{s.correct[hi].mean():.3f} of them')
    hi2 = s.conf_after > 0.9
    print(f'[calib] after: {hi2.sum()} pictures above 0.9, right on '
          f'{s.correct[hi2].mean():.3f} of them')

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.3), facecolor='white')
    for ax, rel, title, colour in (
            (axes[0], s.rel_before, 'Raw scores (before)', GRIP),
            (axes[1], s.rel_after, f'After temperature scaling (T = {s.t:.2f})', SLIDE)):
        _plain(ax)
        mc, acc, cnt, ece = rel
        ax.plot([0, 1], [0, 1], ls='--', color=MUTED, lw=1.2)
        ax.text(0.62, 0.70, 'perfect: score = how\noften it is right', fontsize=9,
                color=MUTED, rotation=0, ha='right')
        keep = cnt >= 20
        width = 0.08
        ax.bar(mc[keep], acc[keep], width=width, color=colour, alpha=0.8, edgecolor=INK,
               lw=0.6)
        for m, a, c in zip(mc[keep], acc[keep], cnt[keep]):
            ax.text(m, a + 0.02, f'{a:.2f}', ha='center', fontsize=8.5, color=INK)
        ax.set_xlim(0, 1.02)
        ax.set_ylim(0, 1.1)
        ax.set_xlabel('the score the model gave (bars at each group\'s average score)',
                      fontsize=9.5)
        ax.set_ylabel('how often it was really right', fontsize=9.5)
        ax.set_title(title, fontsize=11.5, color=INK, weight='bold')
        ax.text(0.03, 1.03, f'average gap (ECE) = {ece:.3f}', fontsize=10, color=colour,
                weight='bold')
    fig.suptitle('Reliability curve on 2,000 simulated test pictures, five classes',
                 fontsize=13, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, UNC_DOC, 'reliability-curve.svg')


# ---------------- ensembles and dropout on a tiny network ----------------

def _mlp_train(x: Arr, y: Arr, seed: int, hidden: int = 50, steps: int = 4000,
               drop: float = 0.0, lr: float = 0.01, wd: float = 1e-4) -> dict[str, Arr]:
    """Train a one-hidden-layer tanh network with Adam, full batch. Optional dropout."""
    rng = np.random.default_rng(seed)
    p = {'w1': rng.normal(0, 1.5, (1, hidden)), 'b1': rng.normal(0, 1.0, hidden),
         'w2': rng.normal(0, 1.0 / np.sqrt(hidden), (hidden, 1)), 'b2': np.zeros(1)}
    m = {k: np.zeros_like(v) for k, v in p.items()}
    v = {k: np.zeros_like(val) for k, val in p.items()}
    X = x[:, None]
    Y = y[:, None]
    for it in range(1, steps + 1):
        h = np.tanh(X @ p['w1'] + p['b1'])
        if drop > 0:
            mask = (rng.uniform(size=h.shape) > drop) / (1 - drop)
            hd = h * mask
        else:
            mask = np.ones_like(h)
            hd = h
        out = hd @ p['w2'] + p['b2']
        err = (out - Y) / len(X)
        g = {'w2': hd.T @ err, 'b2': err.sum(0)}
        dh = (err @ p['w2'].T) * mask * (1 - h ** 2)
        g['w1'] = X.T @ dh
        g['b1'] = dh.sum(0)
        for k in p:
            g[k] = g[k] + wd * p[k]
            m[k] = 0.9 * m[k] + 0.1 * g[k]
            v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            mh = m[k] / (1 - 0.9 ** it)
            vh = v[k] / (1 - 0.999 ** it)
            p[k] = p[k] - lr * mh / (np.sqrt(vh) + 1e-8)
    return p


def _mlp_predict(p: dict[str, Arr], x: Arr, drop: float = 0.0,
                 rng: np.random.Generator | None = None) -> Arr:
    h = np.tanh(x[:, None] @ p['w1'] + p['b1'])
    if drop > 0 and rng is not None:
        h = h * (rng.uniform(size=h.shape) > drop) / (1 - drop)
    return (h @ p['w2'] + p['b2'])[:, 0]


def _grip_force(x: Arr) -> Arr:
    """Made-up truth: grip force (newtons) needed for an object of mass x (kg)."""
    return 6.0 + 18.0 * x + 4.0 * np.sin(4.0 * x)


def ensemble_and_dropout() -> None:
    rng = np.random.default_rng(3)
    x = rng.uniform(0.1, 1.0, 25)
    y = _grip_force(x) + rng.normal(0, 0.8, len(x))
    # scale input and output for training, then undo
    xs = lambda a: (a - 0.8) / 0.5  # noqa: E731
    ym, ysd = y.mean(), y.std()
    grid = np.linspace(0.0, 2.0, 201)

    ens = []
    for k in range(5):
        idx = rng.integers(0, len(x), len(x))
        p = _mlp_train(xs(x[idx]), (y[idx] - ym) / ysd, seed=10 + k)
        ens.append(_mlp_predict(p, xs(grid)) * ysd + ym)
    ens_arr = np.array(ens)

    pd = _mlp_train(xs(x), (y - ym) / ysd, seed=40, drop=0.2)
    drng = np.random.default_rng(99)
    mc = np.array([_mlp_predict(pd, xs(grid), drop=0.2, rng=drng) * ysd + ym
                   for _ in range(100)])

    def at(arr: Arr, xv: float) -> tuple[float, float]:
        i = int(np.argmin(np.abs(grid - xv)))
        return float(arr[:, i].mean()), float(arr[:, i].std())

    for xv in (0.5, 1.5, 2.0):
        em, es = at(ens_arr, xv)
        dm, ds = at(mc, xv)
        print(f'[spread] mass {xv:.1f} kg: truth {_grip_force(np.array([xv]))[0]:.1f} N; '
              f'ensemble {em:.1f} +- {es:.1f} N; dropout {dm:.1f} +- {ds:.1f} N')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0), facecolor='white', sharey=True)
    for ax, arr, title, colour, n_show in (
            (axes[0], ens_arr, 'Ensemble: five networks, trained separately', LINK, 5),
            (axes[1], mc, 'Dropout left on: one network, asked 100 times', PURPLE, 25)):
        _plain(ax)
        ax.axvspan(0.1, 1.0, color='#eef4ea', zorder=0)
        ax.text(0.55, 57, 'where the\ntraining examples are', ha='center', fontsize=9,
                color=SLIDE)
        ax.text(1.5, 57, 'no examples here', ha='center', fontsize=9, color=GRIP)
        for row in arr[:n_show]:
            ax.plot(grid, row, color=colour, lw=1.0, alpha=0.55)
        mean, sd = arr.mean(0), arr.std(0)
        ax.fill_between(grid, mean - 2 * sd, mean + 2 * sd, color=colour, alpha=0.15,
                        label='average ± 2 spreads')
        ax.plot(grid, _grip_force(grid), color=INK, lw=1.4, ls='--', label='the true curve')
        ax.scatter(x, y, s=18, color=INK, zorder=5, label='25 training examples')
        ax.set_xlim(0, 2.0)
        ax.set_ylim(-10, 64)
        ax.set_xlabel('object mass (kg)', fontsize=10)
        ax.set_title(title, fontsize=11.5, weight='bold', color=INK)
        ax.legend(fontsize=8.5, loc='lower right', frameon=False)
    axes[0].set_ylabel('grip force needed (newtons)', fontsize=10)
    fig.suptitle('The answers agree where there were examples, and spread apart where '
                 'there were none', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, UNC_DOC, 'ensemble-spread.svg')


# ---------------- conformal prediction ----------------

def conformal_sets() -> None:
    s = _sim()
    # the calibration pictures: the second 1000 of the validation set (the first
    # 1000 were used to choose the temperature), scored with the scaled model
    cal_p = _softmax(s.val_logits[1000:] / s.t)
    cal_y = s.val_labels[1000:]
    scores = 1.0 - cal_p[np.arange(1000), cal_y]
    alpha = 0.1
    n = len(scores)
    level = np.ceil((n + 1) * (1 - alpha)) / n
    q = float(np.quantile(scores, level, method='higher'))
    keep = s.p_after >= 1.0 - q
    sizes = keep.sum(1)
    covered = keep[np.arange(len(s.test_labels)), s.test_labels]
    print(f'[conformal] alpha {alpha}, n_cal {n}, q = {q:.3f}, include class if p >= {1 - q:.3f}')
    print(f'[conformal] test coverage {covered.mean():.3f}, mean set size {sizes.mean():.2f}')
    for k in range(0, 6):
        print(f'[conformal] sets of size {k}: {(sizes == k).mean():.3f}')
    # the promise is about the average over many draws of calibration pictures:
    # reshuffle the 3,000 scaled pictures 200 times and average the coverage
    pool_p = np.concatenate([cal_p, s.p_after])
    pool_y = np.concatenate([cal_y, s.test_labels])
    srng = np.random.default_rng(11)
    covs = []
    for _ in range(200):
        perm = srng.permutation(len(pool_y))
        c, te = perm[:1000], perm[1000:]
        sc = 1.0 - pool_p[c, pool_y[c]]
        qq = float(np.quantile(sc, level, method='higher'))
        covs.append(float((pool_p[te, pool_y[te]] >= 1.0 - qq).mean()))
    print(f'[conformal] over 200 reshuffles: average coverage {np.mean(covs):.3f}, '
          f'lowest {np.min(covs):.3f}, highest {np.max(covs):.3f}')
    top1 = s.p_after.argmax(1) == s.test_labels
    print(f'[conformal] single best guess right on {top1.mean():.3f}')

    # choose three example test pictures with set sizes 1, 2 and 3
    examples = []
    for want in (1, 2, 3):
        idx = [i for i in range(len(sizes)) if sizes[i] == want and covered[i]]
        examples.append(idx[0])
    for i in examples:
        print(f'[conformal] example {i}: probs '
              + ', '.join(f'{c} {p:.2f}' for c, p in zip(CLASSES, s.p_after[i]))
              + f'; true {CLASSES[s.test_labels[i]]}; set size {sizes[i]}')

    fig = plt.figure(figsize=(14.5, 5.6), facecolor='white')
    gs = fig.add_gridspec(1, 4, width_ratios=[1.5, 1, 1, 1], wspace=0.35)
    ax = fig.add_subplot(gs[0])
    _plain(ax)
    ax.hist(scores, bins=np.linspace(0, 1, 26), color=LINK_PALE, edgecolor=LINK)
    ax.axvline(q, color=GRIP, lw=2)
    ax.text(q - 0.03, ax.get_ylim()[1] * 1.0, f'q = {q:.2f}: 90% of the\nscores are below this',
            color=GRIP, fontsize=9.5, ha='right', va='top',
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})
    ax.set_xlabel('"surprise" = 1 − probability given to the right answer', fontsize=9.5)
    ax.set_ylabel('number of calibration pictures', fontsize=9.5)
    ax.set_title('Step 1: 1,000 calibration pictures', fontsize=11, weight='bold')

    for j, i in enumerate(examples):
        a = fig.add_subplot(gs[j + 1])
        _plain(a)
        probs = s.p_after[i]
        colours = [SLIDE if keep[i, c] else GRID for c in range(5)]
        a.barh(CLASSES[::-1], probs[::-1], color=colours[::-1], edgecolor=INK, lw=0.6)
        a.axvline(1 - q, color=GRIP, lw=1.6, ls='--')
        for c in range(5):
            a.text(max(probs[c], 1 - q) + 0.03, 4 - c, f'{probs[c]:.2f}', va='center', fontsize=9)
        a.set_xlim(0, 1.15)
        a.set_xticks([0, 0.5, 1.0])
        chosen = [CLASSES[c] for c in range(5) if keep[i, c]]
        a.set_title(f'step 2, picture {j + 1}\nset = {{{", ".join(chosen)}}}', fontsize=10.5,
                    weight='bold')
        a.set_xlabel('probability', fontsize=9.5)
        if j == 0:
            a.text(1 - q + 0.03, 4.5, f'keep if ≥ {1 - q:.2f}', color=GRIP, fontsize=9,
                   va='center')
    fig.suptitle('Conformal prediction: step 1 finds the line, step 2 keeps every answer that clears it',
                 fontsize=12.5, weight='bold', color=INK, y=1.02)
    _save(fig, UNC_DOC, 'conformal-sets.svg')


# ---------------- reject option and the cost of being wrong ----------------

def reject_and_cost() -> None:
    s = _sim()
    conf = s.conf_after
    ts = np.linspace(0.2, 0.99, 80)
    cover, err = [], []
    for t in ts:
        m = conf >= t
        cover.append(m.mean())
        err.append(1 - s.correct[m].mean() if m.any() else 0.0)
    for t in (0.0, 0.5, 0.8, 0.9, 0.95):
        m = conf >= t
        print(f'[reject] threshold {t:.2f}: acts on {m.mean():.3f}, '
              f'wrong on {1 - s.correct[m].mean():.3f} of those')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(np.array(cover) * 100, np.array(err) * 100, color=LINK, lw=2)
    for t, colour in ((0.5, JOINT), (0.8, WRIST), (0.95, GRIP)):
        m = conf >= t
        cx, ey = m.mean() * 100, (1 - s.correct[m].mean()) * 100
        ax.scatter([cx], [ey], color=colour, s=50, zorder=5)
        below = t > 0.9
        ax.text(cx + 3.0 if below else cx - 2.0, ey - 0.6 if below else ey + 1.5,
                f'act only if score ≥ {t:.2f}:\n'
                f'acts on {cx:.0f}%, wrong on {ey:.0f}%', fontsize=9, color=colour,
                ha='left' if below else 'right', va='top' if below else 'bottom')
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 25)
    ax.set_xlabel('share of pictures the robot acts on (%)', fontsize=10)
    ax.set_ylabel('share of those it gets wrong (%)', fontsize=10)
    ax.set_title('Declining more often makes the rest more reliable', fontsize=11.5,
                 weight='bold')

    ax = axes[1]
    _plain(ax)
    p = np.linspace(0, 1, 200)
    for c_wrong, c_ask, colour, name in ((2.0, 1.0, SLIDE, 'sponge'),
                                         (50.0, 1.0, GRIP, 'glass')):
        ax.plot(p, (1 - p) * c_wrong, color=colour, lw=2,
                label=f'{name}: act (wrong costs {c_wrong:g})')
        thr = 1 - c_ask / c_wrong
        ax.axvline(thr, color=colour, ls=':', lw=1.4)
        ax.text(thr - 0.01 if name == 'sponge' else thr - 0.16, 8.5 if name == 'sponge' else 4.6,
                f'{name}: act\nabove {thr:.2f}',
                ha='right', color=colour, fontsize=9.5)
    ax.axhline(1.0, color=INK, lw=1.6, ls='--', label='ask a person (costs 1)')
    ax.set_ylim(0, 10)
    ax.set_xlim(0, 1)
    ax.set_xlabel('calibrated probability that the grasp is right', fontsize=10)
    ax.set_ylabel('expected cost (made-up units)', fontsize=10)
    ax.set_title('The threshold comes from the cost of a mistake', fontsize=11.5,
                 weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    fig.tight_layout()
    _save(fig, UNC_DOC, 'reject-and-cost.svg')


# --------------------------------------------------------------------------
# 08_classical-machine-learning: a depth camera's error, learned
# --------------------------------------------------------------------------

def _depth_error(z: Arr) -> Arr:
    """Made-up truth: a depth camera's error (mm) at distance z (m)."""
    return 4.0 * z ** 2 + 3.0 * np.sin(5.0 * z)


NOISE: float = 1.0
Z_LO, Z_HI = 0.3, 1.5


def _make(n: int, rng: np.random.Generator) -> tuple[Arr, Arr]:
    z = rng.uniform(Z_LO, Z_HI, n)
    return z, _depth_error(z) + rng.normal(0, NOISE, n)


def _poly(z: Arr, deg: int) -> Arr:
    u = (z - 0.9) / 0.6
    return np.vander(u, deg + 1, increasing=True)


def ridge_fit(z: Arr, y: Arr, deg: int, lam: float) -> Arr:
    X = _poly(z, deg)
    reg = lam * np.eye(deg + 1)
    reg[0, 0] = 0.0          # do not shrink the constant
    return np.linalg.solve(X.T @ X + reg, X.T @ y)


def ridge_pred(w: Arr, z: Arr) -> Arr:
    return _poly(z, len(w) - 1) @ w


def _rbf(a: Arr, b: Arr, ell: float, sf: float) -> Arr:
    return sf ** 2 * np.exp(-0.5 * (a[:, None] - b[None, :]) ** 2 / ell ** 2)


def gp_fit(z: Arr, y: Arr) -> tuple[float, float, float]:
    """Pick length scale, signal size and noise by the marginal likelihood (grid search)."""
    best = (-np.inf, 0.0, 0.0, 0.0)
    ym = y.mean()
    for ell in (0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.5, 0.7, 1.0):
        for sf in (1.0, 2.0, 4.0, 8.0, 16.0):
            for sn in (0.3, 0.5, 0.8, 1.0, 1.5, 2.5):
                K = _rbf(z, z, ell, sf) + sn ** 2 * np.eye(len(z))
                L = np.linalg.cholesky(K)
                a = np.linalg.solve(L.T, np.linalg.solve(L, y - ym))
                ll = -0.5 * (y - ym) @ a - np.log(np.diag(L)).sum()
                if ll > best[0]:
                    best = (ll, ell, sf, sn)
    return best[1], best[2], best[3]


def gp_pred(z: Arr, y: Arr, zs: Arr, hp: tuple[float, float, float]) -> tuple[Arr, Arr]:
    ell, sf, sn = hp
    ym = y.mean()
    K = _rbf(z, z, ell, sf) + sn ** 2 * np.eye(len(z))
    Ks = _rbf(zs, z, ell, sf)
    L = np.linalg.cholesky(K)
    a = np.linalg.solve(L.T, np.linalg.solve(L, y - ym))
    mean = Ks @ a + ym
    v = np.linalg.solve(L, Ks.T)
    var = sf ** 2 - (v ** 2).sum(0)
    return mean, np.sqrt(np.maximum(var, 0) + sn ** 2)


def _stump_tree(z: Arr, r: Arr, depth: int) -> list[tuple[float, float, float]]:
    """A regression tree on one input, returned as (lo, hi, value) intervals."""
    def grow(lo: float, hi: float, idx: NDArray[np.int64], d: int) -> list[tuple[float, float, float]]:
        if d == 0 or len(idx) < 4:
            return [(lo, hi, float(r[idx].mean()) if len(idx) else 0.0)]
        zi, ri = z[idx], r[idx]
        order = np.argsort(zi)
        zi, ri = zi[order], ri[order]
        best, cut = np.inf, None
        cs = np.cumsum(ri)
        cs2 = np.cumsum(ri ** 2)
        tot, tot2, n = cs[-1], cs2[-1], len(ri)
        for k in range(1, n):
            if zi[k] == zi[k - 1]:
                continue
            sse = (cs2[k - 1] - cs[k - 1] ** 2 / k) + ((tot2 - cs2[k - 1]) - (tot - cs[k - 1]) ** 2 / (n - k))
            if sse < best:
                best, cut = sse, 0.5 * (zi[k] + zi[k - 1])
        if cut is None:
            return [(lo, hi, float(ri.mean()))]
        left = idx[z[idx] <= cut]
        right = idx[z[idx] > cut]
        return grow(lo, cut, left, d - 1) + grow(cut, hi, right, d - 1)
    return grow(-np.inf, np.inf, np.arange(len(z)), depth)


def _tree_pred(tree: list[tuple[float, float, float]], z: Arr) -> Arr:
    out = np.zeros_like(z)
    for lo, hi, v in tree:
        out[(z > lo) & (z <= hi)] = v
    return out


def boost_fit(z: Arr, y: Arr, n_trees: int, rate: float = 0.1,
              depth: int = 2) -> tuple[float, list[list[tuple[float, float, float]]]]:
    base = float(y.mean())
    pred = np.full_like(y, base)
    trees = []
    for _ in range(n_trees):
        t = _stump_tree(z, y - pred, depth)
        trees.append(t)
        pred = pred + rate * _tree_pred(t, z)
    return base, trees


def boost_pred(model: tuple[float, list[list[tuple[float, float, float]]]], z: Arr,
               n: int | None = None, rate: float = 0.1) -> Arr:
    base, trees = model
    out = np.full_like(z, base)
    for t in trees[:n]:
        out = out + rate * _tree_pred(t, z)
    return out


def knn_pred(z: Arr, y: Arr, zs: Arr, k: int) -> Arr:
    k = min(k, len(z))
    d = np.abs(zs[:, None] - z[None, :])
    idx = np.argsort(d, axis=1)[:, :k]
    return y[idx].mean(1)


def mlp_pred_fit(z: Arr, y: Arr, zs: Arr, seed: int) -> Arr:
    ym, ysd = y.mean(), y.std() + 1e-9
    p = _mlp_train((z - 0.9) / 0.6, (y - ym) / ysd, seed=seed, hidden=64, steps=3000,
                   wd=1e-4)
    return _mlp_predict(p, (zs - 0.9) / 0.6) * ysd + ym


def _rmse(a: Arr, b: Arr) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def ridge_vs_plain() -> None:
    rng = np.random.default_rng(21)
    z, y = _make(12, rng)
    zt = np.linspace(Z_LO, Z_HI, 400)
    truth = _depth_error(zt)
    w_plain = ridge_fit(z, y, 9, 0.0)
    w_ridge = ridge_fit(z, y, 9, 0.01)
    w_line = ridge_fit(z, y, 1, 0.0)
    print(f'[ridge] 12 examples, degree 9: plain test RMSE {_rmse(ridge_pred(w_plain, zt), truth):.2f} mm, '
          f'ridge (lambda 0.01) {_rmse(ridge_pred(w_ridge, zt), truth):.2f} mm, '
          f'straight line {_rmse(ridge_pred(w_line, zt), truth):.2f} mm')
    print(f'[ridge] largest weight plain {np.abs(w_plain).max():.1f}, ridge {np.abs(w_ridge).max():.1f}')
    print(f'[ridge] training RMSE plain {_rmse(ridge_pred(w_plain, z), y):.2f}, '
          f'ridge {_rmse(ridge_pred(w_ridge, z), y):.2f}')

    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(zt, truth, color=INK, ls='--', lw=1.3, label='the true error curve')
    ax.plot(zt, ridge_pred(w_line, zt), color=JOINT, lw=1.8,
            label=f'straight line (too simple): off by {_rmse(ridge_pred(w_line, zt), truth):.1f} mm')
    ax.plot(zt, ridge_pred(w_plain, zt), color=GRIP, lw=1.8,
            label=f'wiggly curve, plain fit: off by {_rmse(ridge_pred(w_plain, zt), truth):.1f} mm')
    ax.plot(zt, ridge_pred(w_ridge, zt), color=SLIDE, lw=2.2,
            label=f'same curve with ridge penalty: off by {_rmse(ridge_pred(w_ridge, zt), truth):.1f} mm')
    ax.scatter(z, y, color=INK, s=28, zorder=5, label='12 measured examples')
    ax.set_ylim(-6, 16)
    ax.set_xlabel('distance from the camera (m)', fontsize=10)
    ax.set_ylabel('depth reading error (mm)', fontsize=10)
    ax.set_title('Twelve examples: a small penalty on big weights stops the curve going wild',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    _save(fig, CML_DOC, 'ridge-vs-plain.svg')


def gp_error_bars() -> None:
    rng = np.random.default_rng(5)
    z = np.concatenate([rng.uniform(0.3, 0.8, 8), rng.uniform(1.15, 1.35, 4)])
    y = _depth_error(z) + rng.normal(0, NOISE, len(z))
    hp = gp_fit(z, y)
    zt = np.linspace(0.2, 1.8, 400)
    mean, sd = gp_pred(z, y, zt, hp)
    print(f'[gp] chosen length scale {hp[0]} m, signal size {hp[1]} mm, noise {hp[2]} mm')
    for zq in (0.5, 1.0, 1.25, 1.7):
        i = int(np.argmin(np.abs(zt - zq)))
        print(f'[gp] at {zq:.2f} m: predicts {mean[i]:.1f} +- {2 * sd[i]:.1f} mm (2 sd), '
              f'truth {_depth_error(np.array([zq]))[0]:.1f}')

    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.fill_between(zt, mean - 2 * sd, mean + 2 * sd, color=PURPLE, alpha=0.18,
                    label='error bar: 95% of true values should fall inside')
    ax.plot(zt, mean, color=PURPLE, lw=2, label='Gaussian process prediction')
    ax.plot(zt, _depth_error(zt), color=INK, ls='--', lw=1.2, label='the true error curve')
    ax.scatter(z, y, color=INK, s=28, zorder=5, label='12 measured examples')
    for zq in (0.5, 1.0, 1.7):
        i = int(np.argmin(np.abs(zt - zq)))
        ax.annotate(f'{mean[i]:.1f} ± {2 * sd[i]:.1f} mm', xy=(zq, mean[i] + 2 * sd[i]),
                    xytext=(zq, mean[i] + 2 * sd[i] + 3.5), ha='center', fontsize=9.5,
                    arrowprops={'arrowstyle': '-', 'color': MUTED, 'lw': 0.8})
    ax.set_xlabel('distance from the camera (m)', fontsize=10)
    ax.set_ylabel('depth reading error (mm)', fontsize=10)
    ax.set_ylim(-8, 26)
    ax.set_title('A Gaussian process says how sure it is: narrow near examples, wide in the gaps',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    _save(fig, CML_DOC, 'gp-error-bars.svg')


def trees_and_neighbours() -> None:
    rng = np.random.default_rng(8)
    z, y = _make(40, rng)
    zt = np.linspace(0.2, 1.7, 600)
    model = boost_fit(z, y, 100)
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0), facecolor='white', sharey=True)
    ax = axes[0]
    _plain(ax)
    ax.scatter(z, y, color=INK, s=16, zorder=5, label='40 examples')
    inside = (zt >= Z_LO) & (zt <= Z_HI)
    for n, colour in ((1, JOINT), (10, WRIST), (100, SLIDE)):
        pr = boost_pred(model, zt, n)
        err = _rmse(pr[inside], _depth_error(zt[inside]))
        print(f'[boost] {n} trees: test RMSE {err:.2f} mm')
        ax.step(zt, pr, where='mid', color=colour, lw=1.8,
                label=f'after {n} tree{"s" if n > 1 else ""}: off by {err:.1f} mm')
    ax.axvline(Z_HI, color=MUTED, lw=0.8, ls=':')
    ax.text(Z_HI + 0.02, -3, 'no examples\nbeyond here:\nthe trees go flat', fontsize=9,
            color=MUTED)
    ax.set_title('Gradient-boosted trees', fontsize=11.5, weight='bold')
    ax.set_xlabel('distance from the camera (m)', fontsize=10)
    ax.set_ylabel('depth reading error (mm)', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper left')

    ax = axes[1]
    _plain(ax)
    ax.scatter(z, y, color=INK, s=16, zorder=5, label='40 examples')
    for k, colour in ((1, GRIP), (5, LINK)):
        pr = knn_pred(z, y, zt, k)
        err = _rmse(pr[inside], _depth_error(zt[inside]))
        print(f'[knn] k={k}: test RMSE {err:.2f} mm')
        ax.step(zt, pr, where='mid', color=colour, lw=1.6 if k == 1 else 2.0,
                label=f'k = {k} nearest: off by {err:.1f} mm')
    zq = 1.0
    d = np.abs(z - zq)
    nn = np.argsort(d)[:5]
    print(f'[knn] query {zq} m: 5 nearest at ' + ', '.join(f'{z[i]:.2f}->{y[i]:.1f}' for i in nn)
          + f'; average {y[nn].mean():.1f}, truth {_depth_error(np.array([zq]))[0]:.1f}')
    ax.scatter(z[nn], y[nn], s=90, facecolor='none', edgecolor=LINK, lw=1.6, zorder=6)
    ax.axvline(Z_HI, color=MUTED, lw=0.8, ls=':')
    ax.set_title('k-nearest neighbours', fontsize=11.5, weight='bold')
    ax.set_xlabel('distance from the camera (m)', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_ylim(-5, 17)
    fig.suptitle('Two methods that build their answer from pieces of the data',
                 fontsize=12.5, weight='bold')
    fig.tight_layout()
    _save(fig, CML_DOC, 'trees-and-neighbours.svg')


def small_data_curve() -> None:
    sizes = [10, 20, 40, 80, 160, 320, 640]
    repeats = 8
    zt = np.linspace(Z_LO, Z_HI, 300)
    truth = _depth_error(zt)
    names = ['ridge regression', 'Gaussian process', 'boosted trees', 'k-nearest (k = 5)',
             'small neural network']
    colours = [SLIDE, PURPLE, WRIST, LINK, GRIP]
    res = {nm: [] for nm in names}
    for n in sizes:
        acc = {nm: [] for nm in names}
        for r in range(repeats):
            rng = np.random.default_rng(1000 + 17 * n + r)
            z, y = _make(n, rng)
            acc[names[0]].append(_rmse(ridge_pred(ridge_fit(z, y, 9, 0.01), zt), truth))
            hp = gp_fit(z[:80], y[:80])
            acc[names[1]].append(_rmse(gp_pred(z, y, zt, hp)[0], truth))
            acc[names[2]].append(_rmse(boost_pred(boost_fit(z, y, 100), zt), truth))
            acc[names[3]].append(_rmse(knn_pred(z, y, zt, 5), truth))
            acc[names[4]].append(_rmse(mlp_pred_fit(z, y, zt, seed=r), truth))
        for nm in names:
            res[nm].append(float(np.mean(acc[nm])))
    for nm in names:
        print(f'[curve] {nm:22s} ' + '  '.join(f'n={n}:{v:.2f}' for n, v in zip(sizes, res[nm])))

    fig, ax = plt.subplots(figsize=(10.0, 5.4), facecolor='white')
    _plain(ax)
    for nm, colour in zip(names, colours):
        ax.plot(sizes, res[nm], marker='o', color=colour, lw=2, label=nm)
    ax.set_xscale('log')
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_ylim(0, max(max(v) for v in res.values()) * 1.08)
    ax.set_xlabel('number of training examples (log scale)', fontsize=10)
    ax.set_ylabel('average error of the learned curve (mm)', fontsize=10)
    ax.set_title('Few examples: the Gaussian process is best. By about 80, the network has caught up',
                 fontsize=12, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    _save(fig, CML_DOC, 'small-data-curve.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    reliability_curve()
    ensemble_and_dropout()
    conformal_sets()
    reject_and_cost()
    ridge_vs_plain()
    gp_error_bars()
    trees_and_neighbours()
    small_data_curve()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
