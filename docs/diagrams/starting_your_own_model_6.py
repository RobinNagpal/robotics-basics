"""Generate the diagrams for one page of docs/05_neural-networks/13_starting-your-own-model/.

    06_when-it-does-not-work.md  -> images/starting-your-own-model/when-it-does-not-work/

Run with:  pixi run python ../docs/diagrams/starting_your_own_model_6.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints them so the document can quote the same values.

All the data is simulated. There are three simulated jobs, and the methods run
on them are real ones written in NumPy, which means a real multi-layer network,
real Adam steps, real closed-loop roll-outs and real counted trials.

  1. A reaching job. An arm's gripper has to be driven to an object lying
     somewhere on a table. A written controller plays the demonstrator, its
     commands are recorded with noise that grows with the distance still to go,
     and a network is trained to copy them. The same weights are then run in
     closed loop, which is what gives a task success rate as well as a loss.
  2. An obstacle job, where two demonstrators go round the same obstacle on
     opposite sides, used to show a loss floor that no model size can lower.
  3. A gripper-opening job, where each kind of object has its own shape and its
     own colour, used to show a model that learned the colour rather than the
     shape.
"""

import os

os.environ.setdefault('OMP_NUM_THREADS', '1')      # the machine is shared

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1]
                        / 'images' / 'starting-your-own-model')
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

DOC: str = 'when-it-does-not-work'

Arr = NDArray[np.float64]


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _save(fig: Figure, name: str) -> None:
    out: pathlib.Path = IMAGES / DOC
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    if PNG_DIR is not None:
        fig.savefig(PNG_DIR / f'{DOC}__{name[:-4]}.png', bbox_inches='tight',
                    pad_inches=0.3, facecolor='white', dpi=110)
    plt.close(fig)


def _plain(ax: Axes) -> None:
    ax.set_facecolor('white')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9.5, colors=INK)


def _spearman(x: Arr, y: Arr) -> float:
    """Rank correlation, which says how well an order is preserved."""
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    return float((rx * ry).sum() / np.sqrt((rx ** 2).sum() * (ry ** 2).sum()))


def _interval(k: int, n: int) -> tuple[float, float]:
    """Exact 95% interval for k successes in n trials, by bisection on the
    binomial tail, so that scipy is not needed."""
    log_fact = np.cumsum(np.concatenate([[0.0], np.log(np.arange(1, n + 1))]))

    def _tail(i: NDArray[np.int64], p: float) -> float:
        log_c = log_fact[n] - log_fact[i] - log_fact[n - i]
        return float(np.sum(np.exp(log_c + i * np.log(p) + (n - i) * np.log1p(-p))))

    def tail_le(p: float) -> float:          # P(X <= k) at this p
        return _tail(np.arange(0, k + 1), p)

    def tail_ge(p: float) -> float:          # P(X >= k) at this p
        return _tail(np.arange(k, n + 1), p)

    if k == 0:
        lo = 0.0
    else:
        a, b = 1e-9, 1.0 - 1e-9
        for _ in range(80):
            m = 0.5 * (a + b)
            if tail_ge(m) < 0.025:
                a = m
            else:
                b = m
        lo = 0.5 * (a + b)
    if k == n:
        hi = 1.0
    else:
        a, b = 1e-9, 1.0 - 1e-9
        for _ in range(80):
            m = 0.5 * (a + b)
            if tail_le(m) > 0.025:
                a = m
            else:
                b = m
        hi = 0.5 * (a + b)
    return lo, hi


# --------------------------------------------------------------------------
# job 1: reaching for an object on a table
# --------------------------------------------------------------------------

T: int = 40                 # steps in one attempt
DT: float = 0.05            # seconds a step lasts
GAIN: float = 4.0           # the written controller's gain
VMAX: float = 1.0           # metres a second the arm may be asked for
TOL: float = 0.015          # metres: closer than this at the end is a success


def expert(obj: Arr, grip: Arr) -> Arr:
    """The written controller that plays the demonstrator."""
    a = GAIN * (obj - grip)
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a * np.minimum(1.0, VMAX / np.maximum(n, 1e-9))


def observe(obj: Arr, grip: Arr, step: int, rng: np.random.Generator,
            noise: float = 1.0) -> Arr:
    """The eight numbers the policy is given.

    Four of them are useful (where the object is, where the gripper is), one is
    how far through the attempt we are, one is a distance reading, one is a
    sensor that rarely jumps a long way, and one is pure noise.
    """
    n = len(obj)
    d = np.linalg.norm(obj - grip, axis=1)
    return np.column_stack([
        obj + rng.normal(0, 0.002 * noise, (n, 2)),
        grip + rng.normal(0, 0.002 * noise, (n, 2)),
        np.full(n, step / T),
        d + rng.normal(0, 0.004 * noise, n),
        rng.standard_t(1.6, size=n) * 0.1,
        rng.normal(0, 1.0, n),
    ])


def demos(n_ep: int, rng: np.random.Generator, spread: float = 0.25
          ) -> tuple[Arr, Arr, NDArray[np.int64], Arr]:
    """Record n_ep demonstrated attempts.

    The demonstrator is sloppy when the gripper is far from the object and
    careful when it is close, which is why the recorded command has noise whose
    spread is 0.015 + 0.25 times the distance still to go.
    """
    obj = rng.uniform(-spread, spread, (n_ep, 2))
    grip = rng.uniform(-0.05, 0.05, (n_ep, 2))
    xs, ys, eps, ds = [], [], [], []
    for t in range(T):
        x = observe(obj, grip, t, rng)
        a = expert(obj, grip)
        d = np.linalg.norm(obj - grip, axis=1)
        sig = 0.015 + 0.25 * d
        ys.append(a + rng.normal(0, 1.0, a.shape) * sig[:, None])
        xs.append(x)
        eps.append(np.arange(n_ep))
        ds.append(d)
        grip = grip + DT * a + rng.normal(0, 0.001, grip.shape)
    return (np.concatenate(xs), np.concatenate(ys),
            np.concatenate(eps), np.concatenate(ds))


class MLP:
    """A plain multi-layer network with rectified linear units and Adam."""

    def __init__(self, sizes: list[int], rng: np.random.Generator) -> None:
        self.W = [rng.normal(0, np.sqrt(2.0 / sizes[i]), (sizes[i], sizes[i + 1]))
                  for i in range(len(sizes) - 1)]
        self.b = [np.zeros(sizes[i + 1]) for i in range(len(sizes) - 1)]
        self.m = [np.zeros_like(p) for p in self.W + self.b]
        self.v = [np.zeros_like(p) for p in self.W + self.b]
        self.t = 0
        self.mu: Arr = np.zeros(sizes[0])
        self.sd: Arr = np.ones(sizes[0])

    def __call__(self, x: Arr) -> Arr:
        a = x
        for i in range(len(self.W) - 1):
            a = np.maximum(a @ self.W[i] + self.b[i], 0.0)
        return a @ self.W[-1] + self.b[-1]

    def loss_and_grads(self, x: Arr, y: Arr) -> tuple[float, list[Arr], list[Arr]]:
        acts = [x]
        a = x
        for i in range(len(self.W) - 1):
            a = np.maximum(a @ self.W[i] + self.b[i], 0.0)
            acts.append(a)
        out = a @ self.W[-1] + self.b[-1]
        n = x.shape[0] * y.shape[1]
        loss = float(np.sum((out - y) ** 2) / n)
        g = 2.0 * (out - y) / n
        gw: list[Arr] = [np.zeros(1)] * len(self.W)
        gb: list[Arr] = [np.zeros(1)] * len(self.b)
        for i in range(len(self.W) - 1, -1, -1):
            gw[i] = acts[i].T @ g
            gb[i] = g.sum(axis=0)
            if i > 0:
                g = (g @ self.W[i].T) * (acts[i] > 0)
        return loss, gw, gb

    def step(self, gw: list[Arr], gb: list[Arr], lr: float, wd: float = 0.0) -> None:
        self.t += 1
        k = len(self.W)
        for j, (p, gr) in enumerate(zip(self.W + self.b, gw + gb)):
            if wd and j < k:
                gr = gr + wd * p
            self.m[j] = 0.9 * self.m[j] + 0.1 * gr
            self.v[j] = 0.999 * self.v[j] + 0.001 * gr * gr
            mh = self.m[j] / (1 - 0.9 ** self.t)
            vh = self.v[j] / (1 - 0.999 ** self.t)
            p -= lr * mh / (np.sqrt(vh) + 1e-8)


def standardise(x: Arr, mu: Arr, sd: Arr) -> Arr:
    return (x - mu) / sd


def train(x: Arr, y: Arr, width: int = 32, lr: float = 3e-3, steps: int = 6000,
          seed: int = 0, batch: int = 64, wd: float = 0.0, block: bool = False,
          decay: bool = False, raw: bool = False, every: int = 0,
          held: tuple[Arr, Arr] | None = None,
          mu: Arr | None = None, sd: Arr | None = None
          ) -> tuple[MLP, Arr, Arr]:
    """Train one network and give back its loss curve.

    block=True pretends the first two layers were frozen by accident, which is
    the commonest way a loss stays flat with no error message.
    raw=True leaves the inputs unstandardised.
    """
    rng = np.random.default_rng(seed)
    if mu is None or sd is None:
        mu, sd = x.mean(0), x.std(0) + 1e-12
    if raw:
        mu, sd = np.zeros(x.shape[1]), np.ones(x.shape[1])
    xs = standardise(x, mu, sd)
    net = MLP([x.shape[1], width, width, y.shape[1]], rng)
    net.mu, net.sd = mu, sd
    curve: list[tuple[float, float]] = []
    track: list[tuple[float, float, float]] = []
    for s in range(steps):
        idx = rng.integers(0, len(xs), batch)
        loss, gw, gb = net.loss_and_grads(xs[idx], y[idx])
        if block:
            for i in (0, 1):
                gw[i][:] = 0.0
                gb[i][:] = 0.0
        rate = lr * (0.1 if decay and s > steps // 2 else 1.0)
        net.step(gw, gb, rate, wd)
        if s % max(1, steps // 300) == 0:
            curve.append((s, loss if np.isfinite(loss) else np.nan))
        if every and s % every == 0 and held is not None:
            track.append((s, full_loss(net, xs, y),
                          full_loss(net, standardise(held[0], mu, sd), held[1])))
    return net, np.array(curve), np.array(track) if track else np.zeros((0, 3))


def full_loss(net: MLP, xs: Arr, y: Arr) -> float:
    out = net(xs)
    return float(np.mean((out - y) ** 2))


def held_loss(net: MLP, x: Arr, y: Arr) -> float:
    return full_loss(net, standardise(x, net.mu, net.sd), y)


def rollout(net: MLP, n: int, seed: int, delay: int = 0, drive: float = 1.0,
            cal: float = 0.0, noise: float = 1.0, spread: float = 0.25
            ) -> tuple[Arr, NDArray[np.bool_]]:
    """Run the policy in closed loop n times and say which attempts succeeded."""
    rng = np.random.default_rng(seed)
    obj = rng.uniform(-spread, spread, (n, 2))
    grip = rng.uniform(-0.05, 0.05, (n, 2))
    hist = [np.zeros((n, 2)) for _ in range(delay + 1)]
    dists = []
    for t in range(T):
        x = observe(obj + cal, grip, t, rng, noise)
        a = np.clip(net(standardise(x, net.mu, net.sd)), -VMAX, VMAX)
        hist.append(a)
        grip = grip + DT * hist[-1 - delay] * drive + rng.normal(0, 0.001, grip.shape)
        dists.append(np.linalg.norm(obj - grip, axis=1))
    d = np.array(dists)
    return d, d[-1] < TOL


def two_arms(net: MLP, n: int, seed: int) -> tuple[Arr, Arr]:
    """Run two arms from the same starts, one driven by the policy and one by
    the written controller, and record the policy's command error in both.

    This separates the error the held-out loss measures, which is the error on
    states the demonstrator reached, from the error that decides the task,
    which is the error on states the policy reached itself.
    """
    rng = np.random.default_rng(seed)
    obj = rng.uniform(-0.25, 0.25, (n, 2))
    g_pol = rng.uniform(-0.05, 0.05, (n, 2))
    g_exp = g_pol.copy()
    err_pol, err_exp = [], []
    for t in range(T):
        r2 = np.random.default_rng(90_000 + t)
        xp = observe(obj, g_pol, t, r2)
        xe = observe(obj, g_exp, t, r2)
        ap = np.clip(net(standardise(xp, net.mu, net.sd)), -VMAX, VMAX)
        ae = np.clip(net(standardise(xe, net.mu, net.sd)), -VMAX, VMAX)
        err_pol.append(np.mean((ap - expert(obj, g_pol)) ** 2, axis=1))
        err_exp.append(np.mean((ae - expert(obj, g_exp)) ** 2, axis=1))
        g_pol = g_pol + DT * ap + rng.normal(0, 0.001, g_pol.shape)
        g_exp = g_exp + DT * expert(obj, g_exp) + rng.normal(0, 0.001, g_exp.shape)
    return np.array(err_pol), np.array(err_exp)


# --------------------------------------------------------------------------
# job 2: two ways round one obstacle
# --------------------------------------------------------------------------

def obstacle_demos(n: int, rng: np.random.Generator) -> tuple[Arr, Arr]:
    """n demonstrated paths from left to right past an obstacle at (0, 0).

    Half go above it and half go below it, which is the whole point: the right
    answer is not a single number.
    """
    xs = np.linspace(-0.3, 0.3, 25)
    side = rng.choice([-1.0, 1.0], size=n)
    amp = side * rng.uniform(0.12, 0.18, n)
    paths = (amp[:, None] * np.exp(-(xs[None, :] / 0.16) ** 2)
             + rng.normal(0, 0.004, (n, len(xs))))
    return xs, paths


# --------------------------------------------------------------------------
# job 3: the right gripper opening for a kind of object
# --------------------------------------------------------------------------

N_KINDS: int = 24
SHAPE_NOISE: float = 0.10      # the shape readings are the noisy ones
COLOUR_NOISE: float = 0.01     # the colour readings are crisp
GRASP_TOL: float = 4.0         # millimetres: an opening this close counts as right


def object_kinds(rng: np.random.Generator) -> tuple[Arr, Arr]:
    """Each kind of object has a shape number and a colour number of its own."""
    shape = rng.uniform(0.0, 1.0, N_KINDS)
    colour = rng.permutation(np.linspace(0.0, 1.0, N_KINDS))
    return shape, colour


def object_rows(kinds: NDArray[np.int64], shape: Arr, colour: Arr,
                rng: np.random.Generator) -> tuple[Arr, Arr]:
    """Ten readings per picture: four about the shape, three about the colour
    and three that are noise.  The right opening, in millimetres, depends on
    the shape alone, but the colour readings are far less noisy, so a model is
    pulled towards reading the colour and looking up an answer."""
    s = shape[kinds]
    c = colour[kinds]
    n = len(kinds)
    sn, cn = SHAPE_NOISE, COLOUR_NOISE
    x = np.column_stack([
        s + rng.normal(0, sn, n),
        s ** 2 + rng.normal(0, sn, n),
        np.sin(3 * s) + rng.normal(0, sn, n),
        1.0 - s + rng.normal(0, sn, n),
        c + rng.normal(0, cn, n),
        c ** 2 + rng.normal(0, cn, n),
        np.cos(4 * c) + rng.normal(0, cn, n),
        rng.normal(0, 1.0, n),
        rng.normal(0, 1.0, n),
        rng.normal(0, 1.0, n),
    ])
    y = (20.0 + 60.0 * s)[:, None]
    return x, y


SHAPE_COLS: NDArray[np.int64] = np.array([0, 1, 2, 3])
COLOUR_COLS: NDArray[np.int64] = np.array([4, 5, 6])
NO_COLOUR: NDArray[np.int64] = np.array([0, 1, 2, 3, 7, 8, 9])


# --------------------------------------------------------------------------
# everything computed once
# --------------------------------------------------------------------------

class Sim:
    def __init__(self) -> None:
        print('=' * 72)
        print('job 1: the reaching job')
        self.xtr, self.ytr, self.etr, self.dtr = demos(200, np.random.default_rng(1))
        self.xho, self.yho, self.eho, self.dho = demos(60, np.random.default_rng(2))
        self.mu, self.sd = self.xtr.mean(0), self.xtr.std(0) + 1e-12
        self.noise_var = float(np.mean((0.015 + 0.25 * self.dtr) ** 2))
        self.spread_var = float(np.mean(self.ytr ** 2))
        print(f'  training rows {self.xtr.shape[0]} from 200 attempts, '
              f'held out {self.xho.shape[0]} from 60 attempts')
        print(f'  label noise variance            {self.noise_var:.6f}')
        print(f'  variance of the commands        {self.spread_var:.6f}')


SIM: Sim


# --------------------------------------------------------------------------
# section 1: the loss does not fall at all
# --------------------------------------------------------------------------

def fig_loss_does_not_fall() -> None:
    print('-' * 72)
    print('section 1, picture 1: four runs')
    runs = []
    for label, kw, colour in (
            ('learning rate 1.0, far too large', dict(lr=1.0), GRIP),
            ('learning rate 0.000001, far too small', dict(lr=1e-6), JOINT),
            ('learning rate 0.003, the one that works', dict(lr=3e-3), LINK),
    ):
        net, curve, _ = train(SIM.xtr, SIM.ytr, width=32, steps=3000, seed=0,
                              mu=SIM.mu, sd=SIM.sd, **kw)
        runs.append((label, curve, colour, held_loss(net, SIM.xho, SIM.yho)))
    rng = np.random.default_rng(5)
    yshuf = SIM.ytr[rng.permutation(len(SIM.ytr))]
    net, curve, _ = train(SIM.xtr, yshuf, width=32, lr=3e-3, steps=3000, seed=0,
                          mu=SIM.mu, sd=SIM.sd)
    runs.append(('labels shuffled, learning rate 0.003', curve, PURPLE,
                 float(np.mean((net(standardise(SIM.xho, SIM.mu, SIM.sd))
                                - SIM.yho) ** 2))))

    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    _plain(ax)
    for label, curve, colour, hl in runs:
        y = curve[:, 1].copy()
        print(f'  {label:40s} last batch loss {np.nanmin(y[-5:]):.5f}  '
              f'held out {hl:.5f}')
        ax.plot(curve[:, 0], y, color=colour, lw=2.0, label=label)
    ax.axhline(SIM.spread_var, color=MUTED, ls=':', lw=1.6,
               label=f'answering with zero: {SIM.spread_var:.3f}')
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('loss on the batch (squared metres a second)', fontsize=10)
    ax.set_title('Three flat curves and one that falls, same data and same network',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='center right', framealpha=0.95)
    _save(fig, 'loss-does-not-fall.svg')


def fig_single_batch_test() -> None:
    print('-' * 72)
    print('section 1, picture 2: the single-batch test')
    x8, y8 = SIM.xtr[:8], SIM.ytr[:8]
    rng = np.random.default_rng(6)
    y8s = y8[rng.permutation(8)]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    _plain(ax)
    for label, xa, ya, kw, colour in (
            ('the network as written', x8, y8, {}, LINK),
            ('labels shuffled', x8, y8s, {}, PURPLE),
            ('first two layers frozen by accident', x8, y8, dict(block=True), GRIP),
    ):
        net, curve, _ = train(xa, ya, width=32, lr=3e-3, steps=2000, seed=0,
                              batch=8, mu=SIM.mu, sd=SIM.sd, **kw)
        final = full_loss(net, standardise(xa, SIM.mu, SIM.sd), ya)
        print(f'  {label:36s} final loss on the 8 examples {final:.3e}')
        ax.plot(curve[:, 0], curve[:, 1], color=colour, lw=2.0,
                label=f'{label}  ({final:.1e})')
    ax.set_ylim(1e-13, 30)
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('loss on the same 8 examples', fontsize=10)
    ax.set_title('Eight examples, 2,000 steps: a healthy network drives this to nothing',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='lower left', framealpha=0.95)
    _save(fig, 'single-batch-test.svg')


def fig_learning_rate_band() -> None:
    print('-' * 72)
    print('section 1, picture 3: the learning rate band')
    rates = np.logspace(-7, 0.5, 16)
    out = []
    for lr in rates:
        net, _, _ = train(SIM.xtr, SIM.ytr, width=32, lr=float(lr), steps=1200,
                          seed=0, mu=SIM.mu, sd=SIM.sd)
        hl = held_loss(net, SIM.xho, SIM.yho)
        out.append(hl if np.isfinite(hl) else np.nan)
    out = np.array(out)
    ok = out < SIM.spread_var
    best = int(np.nanargmin(out))
    print(f'  best learning rate {rates[best]:.2e} with held-out loss {out[best]:.5f}')
    print(f'  beats answering with zero from {rates[ok][0]:.2e} to {rates[ok][-1]:.2e}, '
          f'{rates[ok][-1] / rates[ok][0]:.0f} times wide')
    print('  all: ' + ', '.join(f'{r:.1e}:{v:.4f}' for r, v in zip(rates, out)))

    fig, ax = plt.subplots(figsize=(8.0, 4.3))
    _plain(ax)
    ax.axvspan(rates[ok][0], rates[ok][-1], color=LINK_PALE, alpha=0.55,
               label='beats answering with zero')
    ax.plot(rates, out, 'o-', color=LINK, lw=2.0, ms=5.5)
    ax.axhline(SIM.spread_var, color=MUTED, ls=':', lw=1.4)
    ax.text(rates[0], SIM.spread_var * 1.2, f'answering with zero: {SIM.spread_var:.3f}',
            fontsize=9, color=MUTED)
    ax.plot([rates[best]], [out[best]], 'o', ms=12, mfc='none', mec=GRIP, mew=2.0)
    ax.annotate(f'best: {rates[best]:.0e}\n{out[best]:.5f}',
                xy=(rates[best], out[best]), xytext=(-18, 34),
                textcoords='offset points', fontsize=9, color=GRIP,
                ha='center', arrowprops=dict(arrowstyle='-', color=GRIP, lw=1.0))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('learning rate', fontsize=10)
    ax.set_ylabel('held-out loss after 1,200 steps', fontsize=10)
    ax.set_title('Outside a band about a hundred wide, the loss does not fall',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='upper left', framealpha=0.95)
    _save(fig, 'learning-rate-band.svg')


def fig_input_scale() -> None:
    print('-' * 72)
    print('section 1, picture 4: inputs not put on one scale')
    xmm = SIM.xtr.copy()
    xmm[:, 0:4] *= 1000.0                 # positions written in millimetres
    xho = SIM.xho.copy()
    xho[:, 0:4] *= 1000.0
    print('  column spreads as recorded: '
          + ', '.join(f'{v:.3g}' for v in xmm.std(0)))
    print('  column spreads once standardised: '
          + ', '.join(f'{v:.3g}' for v in standardise(xmm, xmm.mean(0),
                                                      xmm.std(0) + 1e-12).std(0)))
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2),
                                  gridspec_kw={'width_ratios': [1.25, 1]})
    _plain(ax)
    _plain(ax2)
    for label, kw, colour in (('left as recorded', dict(raw=True), GRIP),
                              ('standardised first', {}, LINK)):
        net, curve, _ = train(xmm, SIM.ytr, width=32, lr=3e-3, steps=3000,
                              seed=0, **kw)
        hl = float(np.mean((net(standardise(xho, net.mu, net.sd)) - SIM.yho) ** 2))
        print(f'  {label:20s} held-out loss {hl:.5f}')
        ax.plot(curve[:, 0], curve[:, 1], color=colour, lw=2.0,
                label=f'{label}  ({hl:.4f} held out)')
    ax.axhline(SIM.spread_var, color=MUTED, ls=':', lw=1.4)
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('loss on the batch', fontsize=10)
    ax.set_title('Four of the eight inputs written in millimetres',
                 fontsize=11, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='upper right', framealpha=0.95)

    names = ['object x', 'object y', 'grip x', 'grip y', 'phase',
             'distance', 'spiky', 'noise']
    pos = np.arange(8)
    ax2.barh(pos + 0.2, xmm.std(0), height=0.38, color=GRIP, label='as recorded')
    ax2.barh(pos - 0.2, standardise(xmm, xmm.mean(0), xmm.std(0) + 1e-12).std(0),
             height=0.38, color=LINK, label='standardised')
    ax2.set_yticks(pos)
    ax2.set_yticklabels(names, fontsize=9)
    ax2.set_xscale('log')
    ax2.set_xlabel('spread of the column', fontsize=10)
    ax2.set_title('The spreads differ by a factor of thousands',
                  fontsize=11, fontweight='bold', color=INK)
    ax2.grid(axis='x', color=GRID, lw=0.7)
    ax2.set_axisbelow(True)
    ax2.legend(fontsize=9, loc='upper right', framealpha=0.95)
    _save(fig, 'input-scale.svg')


# --------------------------------------------------------------------------
# section 2: the loss falls to a floor and stops
# --------------------------------------------------------------------------

def fig_a_floor_not_a_bug() -> None:
    print('-' * 72)
    print('section 2, picture 1: the floor is the noise in the labels')
    net, curve, track = train(SIM.xtr, SIM.ytr, width=64, lr=3e-3, steps=6000,
                              seed=0, mu=SIM.mu, sd=SIM.sd, every=200,
                              held=(SIM.xho, SIM.yho))
    tl = full_loss(net, standardise(SIM.xtr, SIM.mu, SIM.sd), SIM.ytr)
    hl = held_loss(net, SIM.xho, SIM.yho)
    print(f'  training loss at the end {tl:.6f}, held out {hl:.6f}')
    print(f'  label noise variance     {SIM.noise_var:.6f}')
    print(f'  held-out loss divided by the noise variance {hl / SIM.noise_var:.2f}')
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    _plain(ax)
    ax.plot(track[:, 0], track[:, 1], color=LINK, lw=2.0, label='training loss')
    ax.plot(track[:, 0], track[:, 2], color=WRIST, lw=2.0, label='held-out loss')
    ax.axhline(SIM.noise_var, color=GRIP, ls='--', lw=1.6)
    ax.text(5900, SIM.noise_var * 1.12,
            f'noise in the recorded commands: {SIM.noise_var:.5f}',
            ha='right', fontsize=9.5, color=GRIP)
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('loss (squared metres a second)', fontsize=10)
    ax.set_title('The curve stops at the noise, not at zero, and that is the right answer',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9.5, loc='upper right', framealpha=0.95)
    _save(fig, 'a-floor-not-a-bug.svg')


def fig_floor_and_model_size() -> None:
    print('-' * 72)
    print('section 2, picture 2: does a bigger model lower the floor')
    widths = [1, 2, 4, 8, 16, 32, 64, 128]
    hls, tls = [], []
    for w in widths:
        net, _, _ = train(SIM.xtr, SIM.ytr, width=w, lr=3e-3, steps=6000, seed=0,
                          mu=SIM.mu, sd=SIM.sd)
        hls.append(held_loss(net, SIM.xho, SIM.yho))
        tls.append(full_loss(net, standardise(SIM.xtr, SIM.mu, SIM.sd), SIM.ytr))
    for w, t, h in zip(widths, tls, hls):
        print(f'  width {w:4d}  training {t:.6f}  held out {h:.6f}')
    fig, ax = plt.subplots(figsize=(8.0, 4.3))
    _plain(ax)
    ax.plot(widths, tls, 'o-', color=LINK, lw=2.0, ms=5.5, label='training loss')
    ax.plot(widths, hls, 'o-', color=WRIST, lw=2.0, ms=5.5, label='held-out loss')
    ax.axhline(SIM.noise_var, color=GRIP, ls='--', lw=1.6,
               label=f'noise floor {SIM.noise_var:.5f}')
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(widths)
    ax.set_xticklabels([str(w) for w in widths])
    ax.set_xlabel('units in each hidden layer', fontsize=10)
    ax.set_ylabel('loss at step 6,000', fontsize=10)
    ax.set_title('Width 1 to 4 buys everything, and width 8 to 128 buys nothing',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9.5, loc='upper right', framealpha=0.95)
    _save(fig, 'floor-and-model-size.svg')


def fig_two_ways_round() -> None:
    print('-' * 72)
    print('section 2, picture 3: two ways round one obstacle')
    rng = np.random.default_rng(11)
    xs, paths = obstacle_demos(60, rng)
    mean_path = paths.mean(axis=0)
    radius = 0.06
    clear_demo = np.min(np.abs(paths[:, len(xs) // 2])) - radius
    clear_mean = abs(mean_path[len(xs) // 2]) - radius
    above = paths[paths[:, len(xs) // 2] > 0]
    below = paths[paths[:, len(xs) // 2] < 0]
    loss_mean = float(np.mean((paths - mean_path) ** 2))
    loss_above = float(np.mean((above - above.mean(0)) ** 2))
    print(f'  {len(above)} demonstrations go above and {len(below)} below')
    print(f'  closest any demonstration comes to the obstacle edge: '
          f'{1000 * clear_demo:.1f} mm')
    print(f'  the averaged path misses the edge by {1000 * clear_mean:.1f} mm, '
          'so it goes through the obstacle')
    print(f'  loss of the single averaged answer {loss_mean:.6f}')
    print(f'  loss of one side on its own        {loss_above:.6f}, '
          f'{loss_mean / loss_above:.1f} times smaller')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.2),
                                  gridspec_kw={'width_ratios': [1.3, 1]})
    _plain(ax)
    _plain(ax2)
    circle = plt.Circle((0, 0), radius, color=GRIP, alpha=0.3, zorder=1)
    ax.add_patch(circle)
    ax.add_patch(plt.Circle((0, 0), radius, color=GRIP, fill=False, lw=1.8, zorder=2))
    for p in above[:18]:
        ax.plot(xs, p, color=TEAL, lw=1.0, alpha=0.6, zorder=3)
    for p in below[:18]:
        ax.plot(xs, p, color=PURPLE, lw=1.0, alpha=0.6, zorder=3)
    ax.plot(xs, mean_path, color=INK, lw=2.6, zorder=5,
            label='the one answer that least squares gives')
    ax.plot([], [], color=TEAL, lw=1.4, label=f'{len(above)} demonstrations above')
    ax.plot([], [], color=PURPLE, lw=1.4, label=f'{len(below)} demonstrations below')
    ax.set_xlabel('distance along the table (m)', fontsize=10)
    ax.set_ylabel('sideways offset (m)', fontsize=10)
    ax.set_title('Both ways round are right, and their average is not',
                 fontsize=11, fontweight='bold', color=INK)
    ax.set_ylim(-0.23, 0.23)
    ax.legend(fontsize=8.5, loc='upper left', framealpha=0.95)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)

    bars = [loss_above, loss_mean]
    ax2.bar([0, 1], bars, color=[TEAL, INK], width=0.55)
    for i, v in enumerate(bars):
        ax2.text(i, v * 1.06, f'{v:.5f}', ha='center', fontsize=9.5, color=INK)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['one side\nof the data', 'both sides,\none answer'],
                        fontsize=9.5)
    ax2.set_ylabel('loss the best single answer can reach', fontsize=10)
    ax2.set_ylim(0, max(bars) * 1.25)
    ax2.set_title('The floor is in the data, not the model',
                  fontsize=11, fontweight='bold', color=INK)
    ax2.grid(axis='y', color=GRID, lw=0.7)
    ax2.set_axisbelow(True)
    _save(fig, 'two-ways-round.svg')


def fig_lr_too_high_to_settle() -> None:
    print('-' * 72)
    print('section 2, picture 4: a rate that cannot settle')
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    _plain(ax)
    for label, kw, colour in (
            ('learning rate held at 0.01', dict(lr=1e-2), GRIP),
            ('learning rate 0.01, cut to 0.001 half way', dict(lr=1e-2, decay=True),
             LINK)):
        net, curve, track = train(SIM.xtr, SIM.ytr, width=32, steps=6000, seed=0,
                                  mu=SIM.mu, sd=SIM.sd, every=200,
                                  held=(SIM.xho, SIM.yho), **kw)
        hl = held_loss(net, SIM.xho, SIM.yho)
        print(f'  {label:44s} held-out loss {hl:.6f}')
        ax.plot(track[:, 0], track[:, 2], color=colour, lw=2.0,
                label=f'{label}  ({hl:.5f})')
    ax.axvline(3000, color=MUTED, ls=':', lw=1.3)
    ax.text(3100, 4.2e-3, 'the rate is cut here', fontsize=9, color=MUTED)
    ax.axhline(SIM.noise_var, color=TEAL, ls='--', lw=1.5,
               label=f'noise floor {SIM.noise_var:.5f}')
    ax.set_xlim(800, 6000)
    ax.set_ylim(5e-4, 6e-3)
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('held-out loss', fontsize=10)
    ax.set_title('A floor that one line of code removes',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9.5, loc='upper right', framealpha=0.95)
    _save(fig, 'lr-too-high-to-settle.svg')


# --------------------------------------------------------------------------
# section 3: the held-out loss does not follow
# --------------------------------------------------------------------------

def fig_train_and_held_out_part() -> None:
    print('-' * 72)
    print('section 3, picture 1: the two curves part company')
    xs, ys, _, _ = demos(6, np.random.default_rng(31))
    net, _, track = train(xs, ys, width=128, lr=3e-3, steps=20000, seed=0,
                          every=250, held=(SIM.xho, SIM.yho))
    k = int(np.argmin(track[:, 2]))
    print(f'  6 attempts, {len(xs)} rows, a network of width 128')
    print(f'  best held-out loss {track[k, 2]:.5f} at step {int(track[k, 0])}')
    print(f'  at the end: training {track[-1, 1]:.6f}, held out {track[-1, 2]:.5f}')
    print(f'  held out is {track[-1, 2] / track[k, 2]:.2f} times its best value, '
          f'and {track[-1, 2] / track[-1, 1]:.0f} times the training loss')
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    _plain(ax)
    ax.plot(track[:, 0], track[:, 1], color=LINK, lw=2.0, label='training loss')
    ax.plot(track[:, 0], track[:, 2], color=WRIST, lw=2.0, label='held-out loss')
    ax.plot([track[k, 0]], [track[k, 2]], 'o', ms=11, mfc='none', mec=GRIP, mew=2.0)
    ax.annotate(f'best held out: {track[k, 2]:.4f}\nat step {int(track[k, 0])}',
                xy=(track[k, 0], track[k, 2]), xytext=(-20, -58),
                textcoords='offset points', fontsize=9, color=GRIP, ha='center',
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.1))
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('loss (squared metres a second)', fontsize=10)
    ax.set_title('Six demonstrated attempts and a network of width 128',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9.5, loc='center right', framealpha=0.95)
    _save(fig, 'train-and-held-out-part.svg')


def fig_would_more_data_fix_it() -> None:
    print('-' * 72)
    print('section 3, picture 2: would more attempts fix it')
    counts = [3, 6, 12, 25, 50, 100, 200]
    tls, hls = [], []
    for c in counts:
        xs, ys, _, _ = demos(c, np.random.default_rng(31))
        net, _, _ = train(xs, ys, width=128, lr=3e-3, steps=6000, seed=0)
        tls.append(full_loss(net, standardise(xs, net.mu, net.sd), ys))
        hls.append(held_loss(net, SIM.xho, SIM.yho))
        print(f'  {c:4d} attempts  training {tls[-1]:.6f}  held out {hls[-1]:.6f}  '
              f'gap {hls[-1] / tls[-1]:.1f} times')
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    _plain(ax)
    ax.plot(counts, tls, 'o-', color=LINK, lw=2.0, ms=5.5, label='training loss')
    ax.plot(counts, hls, 'o-', color=WRIST, lw=2.0, ms=5.5, label='held-out loss')
    ax.fill_between(counts, tls, hls, color=LINK_PALE, alpha=0.5)
    ax.axhline(SIM.noise_var, color=GRIP, ls='--', lw=1.5,
               label=f'noise floor {SIM.noise_var:.5f}')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xticks(counts)
    ax.set_xticklabels([str(c) for c in counts])
    ax.set_xlabel('demonstrated attempts in the training set', fontsize=10)
    ax.set_ylabel('loss at step 6,000', fontsize=10)
    ax.set_title('The same network, trained on more attempts: the gap closes',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9.5, loc='upper right', framealpha=0.95)
    _save(fig, 'would-more-data-fix-it.svg')


def fig_which_held_out_set() -> None:
    print('-' * 72)
    print('section 3, picture 3: three held-out sets, one model')
    xs, ys, eps, _ = demos(25, np.random.default_rng(31))
    rng = np.random.default_rng(32)
    pick = rng.permutation(len(xs))[:1200]
    leaky = (xs[pick], ys[pick])                      # rows from training attempts
    fresh = demos(25, np.random.default_rng(33))[:2]  # new attempts, same table
    far = demos(25, np.random.default_rng(34), spread=0.45)[:2]  # a wider table
    sets = [('rows taken from the training attempts', leaky, PURPLE),      # noqa
            ('whole attempts the model never saw', fresh, WRIST),
            ('attempts with the object further out', far, GRIP)]
    net = MLP([8, 128, 128, 2], np.random.default_rng(0))
    mu, sd = xs.mean(0), xs.std(0) + 1e-12
    net.mu, net.sd = mu, sd
    xsn = standardise(xs, mu, sd)
    rng2 = np.random.default_rng(0)
    tracks: list[list[float]] = [[] for _ in range(4)]
    steps_at = []
    for s in range(6000):
        idx = rng2.integers(0, len(xsn), 64)
        _, gw, gb = net.loss_and_grads(xsn[idx], ys[idx])
        net.step(gw, gb, 3e-3)
        if s % 100 == 0:
            steps_at.append(s)
            tracks[0].append(full_loss(net, xsn, ys))
            for i, (_, (hx, hy), _) in enumerate(sets):
                tracks[i + 1].append(full_loss(net, standardise(hx, mu, sd), hy))
    print(f'  training loss at the end {tracks[0][-1]:.6f}')
    for i, (label, _, _) in enumerate(sets):
        print(f'  {label:38s} first {tracks[i + 1][0]:.4f}  '
              f'best {min(tracks[i + 1]):.5f}  end {tracks[i + 1][-1]:.5f}')
    fig, ax = plt.subplots(figsize=(8.6, 4.5))
    _plain(ax)
    ax.plot(steps_at, tracks[0], color=LINK, lw=4.5, alpha=0.45,
            label='training loss')
    for i, (label, _, colour) in enumerate(sets):
        ax.plot(steps_at, tracks[i + 1], color=colour, lw=1.8,
                ls='--' if i == 0 else '-',
                label=f'{label}  ({tracks[i + 1][-1]:.4f})')
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('loss (squared metres a second)', fontsize=10)
    ax.set_title('One run, scored against three different held-out sets',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='upper right', framealpha=0.95)
    _save(fig, 'which-held-out-set.svg')


# --------------------------------------------------------------------------
# section 4: both losses fine, the robot still fails
# --------------------------------------------------------------------------

class Population:
    """Sixty policies trained on the same data, each scored two ways."""

    def __init__(self) -> None:
        print('-' * 72)
        print('section 4: training the population of policies')
        self.rows: list[dict[str, float]] = []
        self.nets: list[MLP] = []
        for width in (4, 8, 16, 32, 64):
            for seed in (0, 1, 2, 3):
                for steps in (600, 2000, 6000):
                    net, _, _ = train(SIM.xtr, SIM.ytr, width=width, lr=3e-3,
                                      steps=steps, seed=seed, mu=SIM.mu, sd=SIM.sd)
                    hl = held_loss(net, SIM.xho, SIM.yho)
                    _, ok = rollout(net, 300, 55)
                    self.rows.append(dict(width=width, seed=seed, steps=steps,
                                          loss=hl, success=float(ok.mean())))
                    self.nets.append(net)
        self.loss = np.array([r['loss'] for r in self.rows])
        self.success = np.array([r['success'] for r in self.rows])
        self.good = self.loss < 0.0015
        print(f'  {len(self.rows)} policies, held-out loss from {self.loss.min():.5f} '
              f'to {self.loss.max():.5f}, success from {self.success.min():.1%} '
              f'to {self.success.max():.1%}')
        print(f'  rank correlation of loss with success, all policies '
              f'{_spearman(self.loss, self.success):.3f}')
        print(f'  the {int(self.good.sum())} policies under 0.0015: loss from '
              f'{self.loss[self.good].min():.5f} to {self.loss[self.good].max():.5f}, '
              f'success from {self.success[self.good].min():.1%} to '
              f'{self.success[self.good].max():.1%}')
        print('  rank correlation of loss with success within that group '
              f'{_spearman(self.loss[self.good], self.success[self.good]):.3f}')
        self.best_loss = int(np.argmin(self.loss))
        self.best_succ = int(np.argmax(self.success))
        print(f'  lowest loss {self.loss[self.best_loss]:.5f} succeeds '
              f'{self.success[self.best_loss]:.1%}')
        print(f'  best success {self.success[self.best_succ]:.1%} has loss '
              f'{self.loss[self.best_succ]:.5f}')
        # the closest pair in loss with the widest gap in success
        idx = np.where(self.good)[0]
        best_pair, best_score = (0, 0), -1.0
        for i in idx:
            for j in idx:
                if self.loss[j] <= self.loss[i]:
                    continue
                if self.loss[j] - self.loss[i] > 0.00004:
                    continue
                gap = self.success[i] - self.success[j]
                if gap > best_score:
                    best_score, best_pair = gap, (int(i), int(j))
        self.pair = best_pair
        a, b = best_pair
        print(f'  pair: loss {self.loss[a]:.5f} succeeds {self.success[a]:.1%} '
              f'(width {self.rows[a]["width"]}, seed {self.rows[a]["seed"]}), '
              f'loss {self.loss[b]:.5f} succeeds {self.success[b]:.1%} '
              f'(width {self.rows[b]["width"]}, seed {self.rows[b]["seed"]})')


POP: Population


def fig_loss_is_not_the_job() -> None:
    print('-' * 72)
    print('section 4, picture 1: held-out loss against success')
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    _plain(ax)
    ax.scatter(POP.loss[~POP.good], 100 * POP.success[~POP.good], s=38,
               color=MUTED, alpha=0.7, label='stopped too early or too small')
    ax.scatter(POP.loss[POP.good], 100 * POP.success[POP.good], s=52,
               color=LINK, alpha=0.9, label='trained to the floor')
    a, b = POP.pair
    for i, colour in ((a, TEAL), (b, GRIP)):
        ax.plot([POP.loss[i]], [100 * POP.success[i]], 'o', ms=14, mfc='none',
                mec=colour, mew=2.2)
    ax.annotate(f'loss {POP.loss[a]:.5f}\nsucceeds {POP.success[a]:.0%}',
                xy=(POP.loss[a], 100 * POP.success[a]), xytext=(42, 10),
                textcoords='offset points', fontsize=9, color=TEAL,
                arrowprops=dict(arrowstyle='->', color=TEAL, lw=1.1))
    ax.annotate(f'loss {POP.loss[b]:.5f}\nsucceeds {POP.success[b]:.0%}',
                xy=(POP.loss[b], 100 * POP.success[b]), xytext=(46, -6),
                textcoords='offset points', fontsize=9, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, lw=1.1))
    ax.set_xscale('log')
    ax.set_xlabel('held-out loss on recorded commands', fontsize=10)
    ax.set_ylabel('attempts that succeeded (%), 300 trials each', fontsize=10)
    ax.set_title('Sixty policies: the loss ranks them, and the arm disagrees',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='upper right', framealpha=0.95)
    _save(fig, 'loss-is-not-the-job.svg')


def fig_what_the_arm_does() -> None:
    print('-' * 72)
    print('section 4, picture 2: what the two policies do on the arm')
    a, b = POP.pair
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.3),
                                  gridspec_kw={'width_ratios': [1.35, 1]})
    _plain(ax)
    _plain(ax2)
    finals = {}
    for i, colour, name in ((a, TEAL, 'the 300-trial winner'),
                            (b, GRIP, 'the other one')):
        d, ok = rollout(POP.nets[i], 300, 55)
        finals[i] = d[-1]
        med = np.median(d, axis=1)
        lo = np.percentile(d, 10, axis=1)
        hi = np.percentile(d, 90, axis=1)
        ax.plot(np.arange(1, T + 1), 1000 * med, color=colour, lw=2.2,
                label=f'{name}: {ok.mean():.0%} succeed')
        ax.fill_between(np.arange(1, T + 1), 1000 * lo, 1000 * hi, color=colour,
                        alpha=0.18)
        print(f'  loss {POP.loss[i]:.5f} success {ok.mean():.1%}  '
              f'median final gap {1000 * np.median(d[-1]):.1f} mm  '
              f'90th percentile {1000 * np.percentile(d[-1], 90):.1f} mm')
    ax.axhline(1000 * TOL, color=INK, ls='--', lw=1.5)
    ax.text(T, 1000 * TOL * 1.12, f'{1000 * TOL:.0f} mm, the tolerance',
            ha='right', fontsize=9.5, color=INK)
    ax.set_yscale('log')
    ax.set_xlabel('step of the attempt', fontsize=10)
    ax.set_ylabel('gap still to close (mm)', fontsize=10)
    ax.set_title('Two policies, almost the same held-out loss',
                 fontsize=11, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='lower left', framealpha=0.95)

    bins = np.linspace(0, 60, 31)
    for i, colour, name in ((a, TEAL, 'the better one'), (b, GRIP, 'the worse one')):
        ax2.hist(1000 * finals[i], bins=bins, color=colour, alpha=0.55, label=name)
    ax2.axvline(1000 * TOL, color=INK, ls='--', lw=1.5)
    ax2.set_xlabel('gap at the last step (mm)', fontsize=10)
    ax2.set_ylabel('attempts', fontsize=10)
    ax2.set_title('Success is a threshold on the last step',
                  fontsize=11, fontweight='bold', color=INK)
    ax2.grid(axis='y', color=GRID, lw=0.7)
    ax2.set_axisbelow(True)
    ax2.legend(fontsize=9, loc='upper right', framealpha=0.95)
    _save(fig, 'what-the-arm-does.svg')


def fig_states_it_reaches_itself() -> None:
    print('-' * 72)
    print('section 4, picture 3: whose states the error is measured on')
    pick = list(np.where(POP.good)[0])
    rec, own, suc = [], [], []
    for i in pick:
        ep, ee = two_arms(POP.nets[i], 200, 55)
        rec.append(float(ee.mean()))
        own.append(float(ep.mean()))
        suc.append(POP.success[i])
        print(f'  loss {POP.loss[i]:.5f}  demonstrator states {rec[-1]:.5f}  '
              f'own states {own[-1]:.5f}  ratio {own[-1] / rec[-1]:5.1f}  '
              f'success {suc[-1]:.1%}')
    rec, own, suc = np.array(rec), np.array(own), np.array(suc)
    sr = _spearman(rec, suc)
    so = _spearman(own, suc)
    print(f'  rank correlation with success: demonstrator states {sr:.3f}, '
          f'own states {so:.3f}')
    print(f'  own-state error is {np.min(own / rec):.2f} to {np.max(own / rec):.1f} '
          'times the demonstrator-state error')
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.3), sharey=True)
    _plain(ax)
    _plain(ax2)
    ax.scatter(rec, 100 * suc, s=55, color=WRIST)
    ax.set_xlabel('error on states the demonstrator reached', fontsize=10)
    ax.set_ylabel('attempts that succeeded (%)', fontsize=10)
    ax.set_title(f'What the held-out loss measures\nrank correlation {sr:+.2f}',
                 fontsize=10.5, fontweight='bold', color=INK)
    ax2.scatter(own, 100 * suc, s=55, color=TEAL)
    ax2.set_xscale('log')
    ax2.set_xticks([1e-3, 2e-3, 5e-3])
    ax2.set_xticklabels(['0.001', '0.002', '0.005'])
    ax2.tick_params(axis='x', which='minor', labelbottom=False)
    ax2.set_xlabel('error on states the policy reached itself', fontsize=10)
    ax2.set_title(f'What the task depends on\nrank correlation {so:+.2f}',
                  fontsize=10.5, fontweight='bold', color=INK)
    for a_ in (ax, ax2):
        a_.grid(color=GRID, lw=0.7)
        a_.set_axisbelow(True)
    _save(fig, 'states-it-reaches-itself.svg')


def fig_how_many_trials() -> None:
    print('-' * 72)
    print('section 4, picture 4: how many trials the number needs')
    a, b = POP.pair
    counts = [10, 20, 50, 100, 200, 400]
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    _plain(ax)
    for off, i, colour in ((-0.14, a, TEAL), (0.14, b, GRIP)):
        for j, n in enumerate(counts):
            _, ok = rollout(POP.nets[i], n, 7000 + n)
            k = int(ok.sum())
            lo, hi = _interval(k, n)
            ax.plot([j + off, j + off], [100 * lo, 100 * hi], color=colour, lw=2.4)
            ax.plot([j + off], [100 * k / n], 'o', color=colour, ms=6)
            if i == a:
                print(f'  winner  {n:4d} trials: {k:4d} successes = {100 * k / n:5.1f}% '
                      f'from {100 * lo:5.1f}% to {100 * hi:5.1f}% '
                      f'({100 * (hi - lo):.1f} points wide)')
            else:
                print(f'  other   {n:4d} trials: {k:4d} successes = {100 * k / n:5.1f}% '
                      f'from {100 * lo:5.1f}% to {100 * hi:5.1f}% '
                      f'({100 * (hi - lo):.1f} points wide)')
    ax.plot([], [], color=TEAL, lw=2.4, label='the better policy')
    ax.plot([], [], color=GRIP, lw=2.4, label='the worse policy')
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels([str(c) for c in counts])
    ax.set_xlabel('trials run', fontsize=10)
    ax.set_ylabel('measured success rate (%) with its 95% range', fontsize=10)
    ax.set_title('Ten trials cannot tell these two policies apart',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9.5, loc='lower right', framealpha=0.95)
    _save(fig, 'how-many-trials.svg')


# --------------------------------------------------------------------------
# section 5: it works on the objects it was trained on
# --------------------------------------------------------------------------

class Objects:
    def __init__(self) -> None:
        print('=' * 72)
        print('job 3: the gripper-opening job')
        rng = np.random.default_rng(41)
        self.shape, self.colour = object_kinds(rng)
        self.train_kinds = np.arange(6)
        self.new_kinds = np.arange(6, 12)
        self.far_kinds = np.arange(18, 24)
        print(f'  {N_KINDS} kinds of object, openings from '
              f'{20.0 + 60.0 * self.shape.min():.1f} to '
              f'{20.0 + 60.0 * self.shape.max():.1f} mm, '
              f'and an answer counts as right within {GRASP_TOL:.0f} mm')

    def rows(self, kinds: NDArray[np.int64], n: int, seed: int) -> tuple[Arr, Arr]:
        rng = np.random.default_rng(seed)
        pick = rng.choice(kinds, size=n)
        return object_rows(pick, self.shape, self.colour, rng)

    def fit(self, x: Arr, y: Arr, seed: int = 0, steps: int = 8000) -> MLP:
        net, _, _ = train(x, y, width=48, lr=3e-3, steps=steps, seed=seed)
        return net

    def score(self, net: MLP, x: Arr, y: Arr) -> float:
        pred = net(standardise(x, net.mu, net.sd))
        return float(np.mean(np.abs(pred - y) < GRASP_TOL))


OBJ: Objects


def fig_per_kind_of_object() -> None:
    print('-' * 72)
    print('section 5, picture 1: the score on each kind of object')
    x, y = OBJ.rows(OBJ.train_kinds, 1800, 42)
    net = OBJ.fit(x, y)
    kinds = list(range(12))
    scores = []
    for k in kinds:
        xk, yk = OBJ.rows(np.array([k]), 300, 500 + k)
        scores.append(OBJ.score(net, xk, yk))
        print(f'  kind {k:2d} (shape {OBJ.shape[k]:.2f}, colour {OBJ.colour[k]:.2f}) '
              f'{"trained on" if k < 6 else "never seen":11s} {scores[-1]:.1%}')
    print(f'  average on the six it trained on {np.mean(scores[:6]):.1%}, '
          f'on the six it never saw {np.mean(scores[6:]):.1%}')
    fig, ax = plt.subplots(figsize=(8.6, 4.3))
    _plain(ax)
    colours = [LINK] * 6 + [GRIP] * 6
    ax.bar(kinds, [100 * s for s in scores], color=colours, width=0.68)
    for k, s in zip(kinds, scores):
        ax.text(k, 100 * s + 1.5, f'{100 * s:.0f}', ha='center', fontsize=9,
                color=INK)
    ax.axhline(100 * float(np.mean(scores[:6])), color=LINK, ls=':', lw=1.4)
    ax.axhline(100 * float(np.mean(scores[6:])), color=GRIP, ls=':', lw=1.4)
    ax.set_xticks(kinds)
    ax.set_xticklabels([f'{k}' for k in kinds], fontsize=9)
    ax.set_xlabel('kind of object', fontsize=10)
    ax.set_ylabel('openings within 4 mm (%)', fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title('Six kinds in the training set (blue) and six it never saw (red)',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    _save(fig, 'per-kind-of-object.svg')


def fig_split_by_kind() -> None:
    print('-' * 72)
    print('section 5, picture 2: the cheapest test is to split by kind')
    x, y = OBJ.rows(OBJ.train_kinds, 1800, 42)
    rng = np.random.default_rng(43)
    perm = rng.permutation(len(x))
    cut = int(0.8 * len(x))
    net_rows = OBJ.fit(x[perm[:cut]], y[perm[:cut]])
    row_score = OBJ.score(net_rows, x[perm[cut:]], y[perm[cut:]])
    four = OBJ.train_kinds[:4]
    two = OBJ.train_kinds[4:]
    xa, ya = OBJ.rows(four, 1800, 44)
    xb, yb = OBJ.rows(two, 600, 45)
    net_kind = OBJ.fit(xa, ya)
    kind_score = OBJ.score(net_kind, xb, yb)
    xn, yn = OBJ.rows(OBJ.new_kinds, 1200, 46)
    truth = OBJ.score(OBJ.fit(x, y), xn, yn)
    print(f'  held-out rows from the same six kinds      {row_score:.1%}')
    print(f'  held-out kinds, two of the six kept back   {kind_score:.1%}')
    print(f'  the six kinds nobody had                   {truth:.1%}')
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    _plain(ax)
    vals = [100 * row_score, 100 * kind_score, 100 * truth]
    ax.bar([0, 1, 2], vals, color=[PURPLE, WRIST, GRIP], width=0.55)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.6, f'{v:.1f}%', ha='center', fontsize=10.5, color=INK)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(['rows held back\nfrom the same kinds',
                        'two of the six kinds\nheld back',
                        'six kinds that were\nnever collected'], fontsize=9.5)
    ax.set_ylabel('openings within 4 mm (%)', fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title('The middle bar costs nothing, and the left bar hides everything',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    _save(fig, 'split-by-kind.svg')


def fig_variety_not_volume() -> None:
    print('-' * 72)
    print('section 5, picture 3: variety against volume, at a fixed total')
    total = 1800
    ks = [1, 2, 3, 4, 6, 9, 12]
    seen, unseen, dots = [], [], []
    xn, yn = OBJ.rows(OBJ.far_kinds, 1200, 47)
    for k in ks:
        s_, u_ = [], []
        for sd in range(4):
            kinds = np.random.default_rng(200 + sd).permutation(18)[:k]
            x, y = OBJ.rows(kinds, total, 48 + k + 7 * sd)
            net = OBJ.fit(x, y, seed=sd)
            s_.append(OBJ.score(net, *OBJ.rows(kinds, 600, 100 + k + sd)))
            u_.append(OBJ.score(net, xn, yn))
        seen.append(float(np.mean(s_)))
        unseen.append(float(np.mean(u_)))
        dots.append(u_)
        print(f'  {k:2d} kinds, {total // k:4d} pictures each: '
              f'on those kinds {seen[-1]:.1%}, on 6 new kinds {unseen[-1]:.1%}  '
              '(runs: ' + ', '.join(f'{v:.0%}' for v in u_) + ')')
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    _plain(ax)
    pos = np.arange(len(ks))
    ax.plot(pos, [100 * s for s in seen], 'o-', color=LINK, lw=2.0, ms=6,
            label='on the kinds it trained on')
    ax.plot(pos, [100 * s for s in unseen], 'o-', color=GRIP, lw=2.0, ms=6,
            label='on six kinds it never saw, averaged over 4 runs')
    for p_, vals in zip(pos, dots):
        ax.plot([p_] * len(vals), [100 * v for v in vals], '.', color=GRIP,
                ms=5, alpha=0.5)
    for p_, s in zip(pos, unseen):
        ax.text(p_, 100 * s + 5.0, f'{100 * s:.0f}', ha='center', fontsize=9,
                color=GRIP)
    ax.set_xticks(pos)
    ax.set_xticklabels([f'{k}\n({total // k} each)' for k in ks], fontsize=9)
    ax.set_xlabel('kinds of object the 1,800 pictures are spread over', fontsize=10)
    ax.set_ylabel('openings within 4 mm (%)', fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title('Same 1,800 pictures every time, spread over more kinds',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9.5, loc='center right', framealpha=0.95)
    _save(fig, 'variety-not-volume.svg')


def fig_which_reading_did_it_use() -> None:
    print('-' * 72)
    print('section 5, picture 4: which readings the model leaned on')
    x, y = OBJ.rows(OBJ.train_kinds, 1800, 42)
    xt, yt = OBJ.rows(OBJ.train_kinds, 600, 600)
    xn, yn = OBJ.rows(OBJ.new_kinds, 600, 601)
    net = OBJ.fit(x, y)
    rng = np.random.default_rng(71)
    plain = OBJ.score(net, xt, yt)
    xc = xt.copy()
    xc[:, COLOUR_COLS] = xc[rng.permutation(len(xc))][:, COLOUR_COLS]
    no_colour = OBJ.score(net, xc, yt)
    xs2 = xt.copy()
    xs2[:, SHAPE_COLS] = xs2[rng.permutation(len(xs2))][:, SHAPE_COLS]
    no_shape = OBJ.score(net, xs2, yt)
    print(f'  on the kinds it trained on: as given {plain:.1%}, '
          f'colour readings scrambled {no_colour:.1%}, '
          f'shape readings scrambled {no_shape:.1%}')
    net2 = OBJ.fit(x[:, NO_COLOUR], y)
    kept = [OBJ.score(net, xt, yt), OBJ.score(net, xn, yn)]
    cut = [OBJ.score(net2, xt[:, NO_COLOUR], yt),
           OBJ.score(net2, xn[:, NO_COLOUR], yn)]
    print(f'  with all ten readings:       trained kinds {kept[0]:.1%}, '
          f'new kinds {kept[1]:.1%}')
    print(f'  colour readings left out:    trained kinds {cut[0]:.1%}, '
          f'new kinds {cut[1]:.1%}')
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.3),
                                  gridspec_kw={'width_ratios': [1.15, 1]})
    _plain(ax)
    _plain(ax2)
    vals = [plain, no_colour, no_shape]
    ax.bar(range(3), [100 * v for v in vals], color=[LINK, JOINT, TEAL], width=0.55)
    for i, v in enumerate(vals):
        ax.text(i, 100 * v + 2.0, f'{100 * v:.1f}%', ha='center', fontsize=10,
                color=INK)
    ax.set_xticks(range(3))
    ax.set_xticklabels(['as given', 'colour readings\nscrambled',
                        'shape readings\nscrambled'], fontsize=9.5)
    ax.set_ylabel('openings within 4 mm (%)', fontsize=10)
    ax.set_ylim(0, 118)
    ax.set_title('The cheap test: hide a group of readings',
                 fontsize=11, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)

    pos = np.arange(2)
    w = 0.33
    ax2.bar(pos - w / 2, [100 * v for v in kept], width=w, color=LINK,
            label='all ten readings')
    ax2.bar(pos + w / 2, [100 * v for v in cut], width=w, color=SLIDE,
            label='colour readings left out')
    for p_, a_, b_ in zip(pos, kept, cut):
        ax2.text(p_ - w / 2, 100 * a_ + 2.0, f'{100 * a_:.0f}%', ha='center',
                 fontsize=9.5, color=INK)
        ax2.text(p_ + w / 2, 100 * b_ + 2.0, f'{100 * b_:.0f}%', ha='center',
                 fontsize=9.5, color=INK)
    ax2.set_xticks(pos)
    ax2.set_xticklabels(['the six kinds\nit trained on', 'six kinds\nit never saw'],
                        fontsize=9.5)
    ax2.set_ylabel('openings within 4 mm (%)', fontsize=10)
    ax2.set_ylim(0, 130)
    ax2.set_title('The fix: train again without them',
                  fontsize=11, fontweight='bold', color=INK)
    ax2.grid(axis='y', color=GRID, lw=0.7)
    ax2.set_axisbelow(True)
    ax2.legend(fontsize=9, loc='upper center', framealpha=0.95)
    _save(fig, 'which-reading-did-it-use.svg')


# --------------------------------------------------------------------------
# section 6: it works in the simulator and not on the arm
# --------------------------------------------------------------------------

REAL = dict(delay=2, drive=0.85, cal=0.012, noise=3.0)


def fig_one_difference_at_a_time() -> None:
    print('-' * 72)
    print('section 6, picture 1: one difference at a time')
    net, _, _ = train(SIM.xtr, SIM.ytr, width=32, lr=3e-3, steps=6000, seed=0,
                      mu=SIM.mu, sd=SIM.sd)
    cases = [('the simulator it trained in', {}),
             ('noisier sensors', dict(noise=REAL['noise'])),
             ('the object 12 mm off', dict(cal=REAL['cal'])),
             ('two periods of delay', dict(delay=REAL['delay'])),
             ('15% weaker drive', dict(drive=REAL['drive'])),
             ('all four together', dict(REAL))]
    vals = []
    for label, kw in cases:
        _, ok = rollout(net, 600, 61, **kw)
        vals.append(float(ok.mean()))
        print(f'  {label:30s} {vals[-1]:.1%}')
    print(f'  the four separate drops add to '
          f'{sum(vals[0] - v for v in vals[1:5]):.1%} of the {vals[0]:.1%} '
          f'it started with, and together they cost {vals[0] - vals[5]:.1%}')
    fig, ax = plt.subplots(figsize=(8.8, 4.3))
    _plain(ax)
    colours = [LINK] + [JOINT] * 4 + [GRIP]
    ax.bar(range(len(vals)), [100 * v for v in vals], color=colours, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, 100 * v + 1.8, f'{100 * v:.1f}%', ha='center', fontsize=10,
                color=INK)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels([c[0].replace(' ', '\n', 1) for c in cases], fontsize=9)
    ax.set_ylabel('attempts that succeeded (%), 600 trials', fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title('Putting each real-world difference into the simulator, one at a time',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    _save(fig, 'one-difference-at-a-time.svg')


def fig_delay_costs_success() -> None:
    print('-' * 72)
    print('section 6, picture 2: what one period of delay costs')
    net, _, _ = train(SIM.xtr, SIM.ytr, width=32, lr=3e-3, steps=6000, seed=0,
                      mu=SIM.mu, sd=SIM.sd)
    delays = list(range(0, 7))
    vals, gaps = [], []
    for d in delays:
        dd, ok = rollout(net, 800, 61, delay=d)
        vals.append(float(ok.mean()))
        gaps.append(float(np.median(dd[-1])))
        print(f'  {d} periods ({1000 * d * DT:.0f} ms): success {vals[-1]:.1%}, '
              f'median final gap {1000 * gaps[-1]:.1f} mm')
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    _plain(ax)
    ax.plot(delays, [100 * v for v in vals], 'o-', color=GRIP, lw=2.2, ms=6.5)
    for d, v in zip(delays, vals):
        ax.text(d, 100 * v + 3.0, f'{100 * v:.0f}%', ha='center', fontsize=9.5,
                color=INK)
    ax2 = ax.twinx()
    ax2.plot(delays, [1000 * g for g in gaps], 's--', color=TEAL, lw=1.6, ms=5)
    ax2.set_ylabel('median gap at the last step (mm)', fontsize=10, color=TEAL)
    ax2.tick_params(labelsize=9.5, colors=TEAL)
    ax2.spines['top'].set_visible(False)
    ax.set_xticks(delays)
    ax.set_xticklabels([f'{d}\n({1000 * d * DT:.0f} ms)' for d in delays], fontsize=9)
    ax.set_xlabel('control periods of delay added, at 20 commands a second', fontsize=10)
    ax.set_ylabel('attempts that succeeded (%)', fontsize=10, color=GRIP)
    ax.set_ylim(0, 112)
    ax.set_title('Delay the simulator did not have, added back one period at a time',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    _save(fig, 'delay-costs-success.svg')


def fig_randomise_what_you_do_not_know() -> None:
    print('-' * 72)
    print('section 6, picture 3: training across the range instead of at one point')
    rng = np.random.default_rng(63)
    xs, ys = SIM.xtr, SIM.ytr
    # The randomised set records the same job in eight simulators whose sensor
    # noise, calibration, delay and drive strength are each drawn from a range
    # that covers, but does not name, the real arm's values.
    xs2, ys2 = [], []
    settings = []
    for i in range(8):
        r = np.random.default_rng(400 + i)
        obj = r.uniform(-0.25, 0.25, (25, 2))
        grip = r.uniform(-0.05, 0.05, (25, 2))
        noise = float(rng.uniform(0.5, 4.0))
        cal = 0.0                      # a fixed offset is measured, not randomised
        delay = int(rng.integers(0, 4))
        drive = float(rng.uniform(0.80, 1.10))
        settings.append((noise, cal, delay, drive))
        hist = [np.zeros((25, 2)) for _ in range(delay + 1)]
        for t in range(T):
            x = observe(obj + cal, grip, t, r, noise)
            a = expert(obj, grip)
            d = np.linalg.norm(obj - grip, axis=1)
            sig = 0.015 + 0.25 * d
            xs2.append(x)
            ys2.append(a + r.normal(0, 1.0, a.shape) * sig[:, None])
            hist.append(a)
            grip = grip + DT * hist[-1 - delay] * drive + r.normal(0, 0.001,
                                                                   grip.shape)
    xs2 = np.concatenate(xs2)
    ys2 = np.concatenate(ys2)
    print(f'  nominal training set {xs.shape[0]} rows, '
          f'randomised training set {xs2.shape[0]} rows')
    print('  the eight settings drawn (sensor noise, calibration in mm, '
          'delay in periods, drive):')
    for s in settings:
        print(f'    noise x{s[0]:.1f}  cal {1000 * s[1]:+5.1f} mm  '
              f'delay {s[2]}  drive {s[3]:.2f}')
    out = {}
    for name, (a, b) in (('trained at one setting', (xs, ys)),
                         ('trained across a range', (xs2, ys2))):
        net, _, _ = train(a, b, width=32, lr=3e-3, steps=6000, seed=0)
        _, ok_sim = rollout(net, 600, 61)
        _, ok_real = rollout(net, 600, 61, **REAL)
        out[name] = (float(ok_sim.mean()), float(ok_real.mean()))
        print(f'  {name:24s} simulator {out[name][0]:.1%}  arm {out[name][1]:.1%}')
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    _plain(ax)
    pos = np.arange(2)
    w = 0.32
    names = list(out)
    ax.bar(pos - w / 2, [100 * out[n][0] for n in names], width=w, color=LINK,
           label='run in the simulator it trained in')
    ax.bar(pos + w / 2, [100 * out[n][1] for n in names], width=w, color=GRIP,
           label='run with the four real differences')
    for p_, n in zip(pos, names):
        ax.text(p_ - w / 2, 100 * out[n][0] + 1.8, f'{100 * out[n][0]:.0f}%',
                ha='center', fontsize=10, color=INK)
        ax.text(p_ + w / 2, 100 * out[n][1] + 1.8, f'{100 * out[n][1]:.0f}%',
                ha='center', fontsize=10, color=INK)
    ax.set_xticks(pos)
    ax.set_xticklabels(['trained at one setting', 'trained across a range'],
                       fontsize=10)
    ax.set_ylabel('attempts that succeeded (%), 600 trials', fontsize=10)
    ax.set_ylim(0, 132)
    ax.set_title('The same amount of data, recorded under a spread of settings',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='upper center', ncol=2, framealpha=0.95)
    _save(fig, 'randomise-what-you-do-not-know.svg')


# --------------------------------------------------------------------------
# section 7: it worked last week, and the discipline
# --------------------------------------------------------------------------

def fig_same_weights_different_answer() -> None:
    print('-' * 72)
    print('section 7, picture 1: one unchanged policy, eight evaluations')
    net, _, _ = train(SIM.xtr, SIM.ytr, width=32, lr=3e-3, steps=6000, seed=0,
                      mu=SIM.mu, sd=SIM.sd)
    ks, ns = [], 25
    for r in range(8):
        _, ok = rollout(net, ns, 8000 + r)
        ks.append(int(ok.sum()))
    pooled_k, pooled_n = sum(ks), ns * 8
    lo, hi = _interval(pooled_k, pooled_n)
    print(f'  eight runs of {ns} trials each: ' + ', '.join(f'{100 * k / ns:.0f}%'
                                                            for k in ks))
    print(f'  lowest {100 * min(ks) / ns:.0f}%, highest {100 * max(ks) / ns:.0f}%, '
          f'a spread of {100 * (max(ks) - min(ks)) / ns:.0f} points '
          'with nothing changed')
    print(f'  all 200 trials pooled: {pooled_k} of {pooled_n} = '
          f'{100 * pooled_k / pooled_n:.1f}% from {100 * lo:.1f}% to {100 * hi:.1f}%')
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    _plain(ax)
    for r, k in enumerate(ks):
        klo, khi = _interval(k, ns)
        ax.plot([r, r], [100 * klo, 100 * khi], color=MUTED, lw=2.0)
        ax.plot([r], [100 * k / ns], 'o', color=LINK, ms=8)
        ax.text(r, 100 * k / ns + 3.4, f'{100 * k / ns:.0f}%', ha='center',
                fontsize=9.5, color=INK)
    ax.axhspan(100 * lo, 100 * hi, color=LINK_PALE, alpha=0.5,
               label=f'all 200 trials together: {100 * pooled_k / pooled_n:.1f}% '
                     f'({100 * lo:.1f}% to {100 * hi:.1f}%)')
    ax.axhline(100 * pooled_k / pooled_n, color=TEAL, lw=1.6)
    ax.set_xticks(range(8))
    ax.set_xticklabels([f'week {r + 1}' for r in range(8)], fontsize=9)
    ax.set_ylabel('measured success rate (%)', fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title('The same weights, the same arm, 25 trials each time',
                 fontsize=11.5, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, loc='lower right', framealpha=0.95)
    _save(fig, 'same-weights-different-answer.svg')


def fig_the_spread_between_seeds() -> None:
    print('-' * 72)
    print('section 7, picture 2: the spread between seeds')
    losses, succs = [], []
    for seed in range(8):
        net, _, _ = train(SIM.xtr, SIM.ytr, width=32, lr=3e-3, steps=6000,
                          seed=seed, mu=SIM.mu, sd=SIM.sd)
        _, ok = rollout(net, 400, 66)
        losses.append(held_loss(net, SIM.xho, SIM.yho))
        succs.append(float(ok.mean()))
        print(f'  seed {seed}: held-out loss {losses[-1]:.5f}, success {succs[-1]:.1%}')
    print(f'  loss from {min(losses):.5f} to {max(losses):.5f}, a spread of '
          f'{100 * (max(losses) / min(losses) - 1):.0f}%')
    print(f'  success from {min(succs):.1%} to {max(succs):.1%}, a spread of '
          f'{100 * (max(succs) - min(succs)):.0f} points')
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.4, 4.2))
    _plain(ax)
    _plain(ax2)
    ax.bar(range(8), losses, color=WRIST, width=0.6)
    ax.axhline(float(np.mean(losses)), color=INK, ls=':', lw=1.4)
    ax.set_xticks(range(8))
    ax.set_xticklabels([str(s) for s in range(8)], fontsize=9.5)
    ax.set_xlabel('starting seed', fontsize=10)
    ax.set_ylabel('held-out loss', fontsize=10)
    ax.set_ylim(0, max(losses) * 1.3)
    ax.set_title(f'Held-out loss: {min(losses):.5f} to {max(losses):.5f}',
                 fontsize=11, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax2.bar(range(8), [100 * s for s in succs], color=GRIP, width=0.6)
    for s, v in enumerate(succs):
        ax2.text(s, 100 * v + 1.8, f'{100 * v:.0f}', ha='center', fontsize=9,
                 color=INK)
    ax2.axhline(100 * float(np.mean(succs)), color=INK, ls=':', lw=1.4)
    ax2.set_xticks(range(8))
    ax2.set_xticklabels([str(s) for s in range(8)], fontsize=9.5)
    ax2.set_xlabel('starting seed', fontsize=10)
    ax2.set_ylabel('attempts that succeeded (%)', fontsize=10)
    ax2.set_ylim(0, 112)
    ax2.set_title(f'Success rate: {min(succs):.0%} to {max(succs):.0%}',
                  fontsize=11, fontweight='bold', color=INK)
    ax2.grid(axis='y', color=GRID, lw=0.7)
    ax2.set_axisbelow(True)
    _save(fig, 'the-spread-between-seeds.svg')


def fig_two_changes_at_once() -> None:
    print('-' * 72)
    print('section 7, picture 3: two changes at once')
    base = demos(25, np.random.default_rng(31))
    more = demos(200, np.random.default_rng(31))
    seeds = (0, 1, 2, 3)
    cells: dict[tuple[str, str], float] = {}
    runs: dict[tuple[str, str], list[float]] = {}
    for a_name, data in (('25 attempts', base), ('200 attempts', more)):
        for b_name, wd in (('no weight decay', 0.0), ('weight decay 0.001', 0.001)):
            succ = []
            for seed in seeds:
                net, _, _ = train(data[0], data[1], width=32, lr=3e-3, steps=6000,
                                  seed=seed, wd=wd)
                _, ok = rollout(net, 400, 67)
                succ.append(float(ok.mean()))
            cells[(a_name, b_name)] = float(np.mean(succ))
            runs[(a_name, b_name)] = succ
            print(f'  {a_name:13s} + {b_name:19s} success '
                  f'{cells[(a_name, b_name)]:.1%}  (seeds: '
                  + ', '.join(f'{s:.0%}' for s in succ) + ')')
    key_base = ('25 attempts', 'no weight decay')
    key_both = ('200 attempts', 'weight decay 0.001')
    key_a = ('200 attempts', 'no weight decay')
    key_b = ('25 attempts', 'weight decay 0.001')
    base_v, both_v = cells[key_base], cells[key_both]
    only_a, only_b = cells[key_a], cells[key_b]
    print(f'  changing both at once: {base_v:.1%} -> {both_v:.1%}, '
          f'a gain of {100 * (both_v - base_v):.1f} points')
    print(f'  more attempts alone  : {base_v:.1%} -> {only_a:.1%}, '
          f'{100 * (only_a - base_v):+.1f} points')
    print(f'  weight decay alone   : {base_v:.1%} -> {only_b:.1%}, '
          f'{100 * (only_b - base_v):+.1f} points')
    paired = sum(1 for p, q in zip(runs[key_a], runs[key_both]) if q < p)
    print(f'  with 200 attempts, the weight decay made it worse in {paired} '
          f'of the {len(seeds)} runs')
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.3),
                                  gridspec_kw={'width_ratios': [1, 1.5]})
    _plain(ax)
    _plain(ax2)
    jit = np.linspace(-0.12, 0.12, len(seeds))
    ax.bar([0, 1], [100 * base_v, 100 * both_v], color=[MUTED, SLIDE], width=0.5)
    for i, key in enumerate([key_base, key_both]):
        top = max(100 * cells[key], 100 * max(runs[key]))
        ax.text(i, top + 3.0, f'{100 * cells[key]:.1f}%',
                ha='center', fontsize=10.5, color=INK)
        ax.plot(i + jit, [100 * v for v in runs[key]], '.', color=INK,
                ms=7, alpha=0.65)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['where you\nstarted', 'both changes\nat once'], fontsize=9.5)
    ax.set_ylabel('attempts that succeeded (%)', fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title('Two changes at once',
                 fontsize=11, fontweight='bold', color=INK)
    ax.grid(axis='y', color=GRID, lw=0.7)
    ax.set_axisbelow(True)

    labels = ['where you\nstarted', 'more\nattempts', 'weight\ndecay', 'both\nchanges']
    keys = [key_base, key_a, key_b, key_both]
    ax2.bar(range(4), [100 * cells[k] for k in keys],
            color=[MUTED, LINK, GRIP, SLIDE], width=0.58)
    for i, key in enumerate(keys):
        top = max(100 * cells[key], 100 * max(runs[key]))
        ax2.text(i, top + 3.0, f'{100 * cells[key]:.1f}%',
                 ha='center', fontsize=10, color=INK)
        ax2.plot(i + jit, [100 * v for v in runs[key]], '.', color=INK,
                 ms=7, alpha=0.65)
    ax2.axhline(100 * base_v, color=MUTED, ls=':', lw=1.4)
    ax2.set_xticks(range(4))
    ax2.set_xticklabels(labels, fontsize=9.5)
    ax2.set_ylabel('attempts that succeeded (%)', fontsize=10)
    ax2.set_ylim(0, 112)
    ax2.set_title('One change at a time, four runs each, the runs drawn as dots',
                  fontsize=11, fontweight='bold', color=INK)
    ax2.grid(axis='y', color=GRID, lw=0.7)
    ax2.set_axisbelow(True)
    _save(fig, 'two-changes-at-once.svg')


# --------------------------------------------------------------------------

def main() -> None:
    global PNG_DIR, SIM, POP, OBJ
    if '--png' in sys.argv:
        PNG_DIR = pathlib.Path(sys.argv[sys.argv.index('--png') + 1])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    SIM = Sim()
    fig_loss_does_not_fall()
    fig_single_batch_test()
    fig_learning_rate_band()
    fig_input_scale()
    fig_a_floor_not_a_bug()
    fig_floor_and_model_size()
    fig_two_ways_round()
    fig_lr_too_high_to_settle()
    fig_train_and_held_out_part()
    fig_would_more_data_fix_it()
    fig_which_held_out_set()
    POP = Population()
    fig_loss_is_not_the_job()
    fig_what_the_arm_does()
    fig_states_it_reaches_itself()
    fig_how_many_trials()
    OBJ = Objects()
    fig_per_kind_of_object()
    fig_split_by_kind()
    fig_variety_not_volume()
    fig_which_reading_did_it_use()
    print('=' * 72)
    print('sections 6 and 7')
    fig_one_difference_at_a_time()
    fig_delay_costs_success()
    fig_randomise_what_you_do_not_know()
    fig_same_weights_different_answer()
    fig_the_spread_between_seeds()
    fig_two_changes_at_once()
    print('=' * 72)
    print('done')


if __name__ == '__main__':
    main()
