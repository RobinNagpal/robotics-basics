"""Generate the diagrams for the last two pages of docs/06_neural-networks/07_pretraining-and-adapting/.

    03_fine-tuning-and-adapters.md            -> images/pretraining-and-adapting/fine-tuning-and-adapters/
    04_making-a-model-smaller-and-faster.md   -> images/pretraining-and-adapting/making-a-model-smaller-and-faster/

Run with:  python3 docs/diagrams/pretraining_and_adapting_2.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints all of them so the two documents can quote the same values.

Two kinds of number appear here.

The parameter counts, the memory sizes, the low-rank adapter counts and the
quantisation step sizes are exact arithmetic on a stated transformer shape
(32 blocks, width 4096, 32 heads, feed-forward inner width 11008, vocabulary
32000) and on stated byte costs. Nothing there is simulated, although the
graphics-card memory, the memory bandwidth and the arithmetic rate used for
the speed pictures are stated assumptions, and the pictures say so.

The learning experiments are simulated. A six-class problem of
eight-dimensional feature vectors is drawn from Gaussian blobs with
numpy.random.default_rng, a small fully connected network is trained on it in
NumPy, and the fine-tuning, forgetting, quantisation, distillation and pruning
experiments are then run on that network for real. The methods are real
(softmax cross-entropy training with momentum, low-rank adapter training,
symmetric per-channel and grouped quantisation, straight-through
quantisation-aware training, soft-target distillation, magnitude pruning,
whole-neuron pruning and 2:4 sparsity); only the data is made up.
"""

import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = pathlib.Path(__file__).resolve().parents[1] / 'images' / 'pretraining-and-adapting'
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

FT_DOC: str = 'fine-tuning-and-adapters'
SM_DOC: str = 'making-a-model-smaller-and-faster'

Arr = NDArray[np.float64]
Ints = NDArray[np.int64]


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


def _blank(ax: Axes) -> None:
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


def _softmax(z: Arr) -> Arr:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def _gib(nbytes: float) -> float:
    return nbytes / 2 ** 30


def _big(n: float) -> str:
    """Write a count the way the pages write it."""
    if n >= 1e9:
        return f'{n / 1e9:.2f} billion'
    if n >= 1e6:
        return f'{n / 1e6:.2f} million'
    if n >= 1e3:
        return f'{n / 1e3:.1f} thousand'
    return f'{n:.0f}'


# ==========================================================================
# PART 1.  The stated transformer shape, and exact parameter and byte counts.
# ==========================================================================

D_MODEL: int = 4096
N_BLOCK: int = 32
D_FF: int = 11008
VOCAB: int = 32000

EMB: int = VOCAB * D_MODEL
ATT_PER_BLOCK: int = 4 * D_MODEL * D_MODEL          # query, key, value, output
FF_PER_BLOCK: int = 3 * D_MODEL * D_FF              # gate, up, down
NORM_PER_BLOCK: int = 2 * D_MODEL
BLOCK: int = ATT_PER_BLOCK + FF_PER_BLOCK + NORM_PER_BLOCK
BLOCKS: int = N_BLOCK * BLOCK
FINAL_NORM: int = D_MODEL
OUT_HEAD: int = VOCAB * D_MODEL
TOTAL: int = EMB + BLOCKS + FINAL_NORM + OUT_HEAD

# bytes a parameter costs during training, under one common recipe:
# the weight in bfloat16 (2), its gradient in bfloat16 (2) and two float32
# running averages for the AdamW optimiser (4 + 4).
B_FROZEN: int = 2
B_TRAIN: int = 2 + 2 + 4 + 4
CARD_GIB: float = 24.0

HEAD_OUT: int = 6                                   # a new 6-way output head
NEW_HEAD: int = D_MODEL * HEAD_OUT + HEAD_OUT
LORA_R: int = 8
LORA_QV: int = N_BLOCK * 2 * (LORA_R * D_MODEL + D_MODEL * LORA_R)
UNFROZEN_BLOCKS: int = 4
LAST_BLOCKS: int = UNFROZEN_BLOCKS * BLOCK

RUNGS: list[str] = ['better prompt', 'head on frozen\nfeatures',
                    f'LoRA, rank {LORA_R},\nquery and value', 'unfreeze last\n4 blocks',
                    'full fine-tune']
RUNG_TRAIN: list[int] = [0, NEW_HEAD, LORA_QV, LAST_BLOCKS, TOTAL]
RUNG_EXTRA: list[int] = [0, NEW_HEAD, LORA_QV, 0, 0]     # parameters that are new, not part of TOTAL


def rung_memory(trainable: int, extra: int) -> float:
    """Bytes of weights, gradients and optimiser state for one rung."""
    base_frozen = TOTAL - (trainable - extra)
    return base_frozen * B_FROZEN + trainable * B_TRAIN


RUNG_BYTES: list[float] = [rung_memory(t, e) for t, e in zip(RUNG_TRAIN, RUNG_EXTRA)]


def report_shape() -> None:
    print('--- the stated model shape ---')
    print(f'embedding table        {EMB:>15,}')
    print(f'attention per block    {ATT_PER_BLOCK:>15,}')
    print(f'feed-forward per block {FF_PER_BLOCK:>15,}')
    print(f'norms per block        {NORM_PER_BLOCK:>15,}')
    print(f'one block              {BLOCK:>15,}')
    print(f'32 blocks              {BLOCKS:>15,}')
    print(f'final norm             {FINAL_NORM:>15,}')
    print(f'output head            {OUT_HEAD:>15,}')
    print(f'TOTAL                  {TOTAL:>15,}   ({_big(TOTAL)})')
    print(f'bf16 weights only      {_gib(TOTAL * 2):.3f} GiB')
    print('--- the five rungs ---')
    for name, tr, by in zip(RUNGS, RUNG_TRAIN, RUNG_BYTES):
        pct = 100.0 * tr / TOTAL
        print(f'{name.replace(chr(10), " "):36s} trainable {tr:>13,}  '
              f'({pct:8.4f}% of the model)  memory {_gib(by):7.2f} GiB')
    fits = int((CARD_GIB * 2 ** 30 - TOTAL * B_FROZEN) // (BLOCK * (B_TRAIN - B_FROZEN)))
    print(f'blocks that can be unfrozen inside {CARD_GIB:.0f} GiB: {fits}')


# --- arithmetic cost of a longer prompt against a one-off fine-tune -------

PROMPT_TOKENS: int = 600
FT_EXAMPLES: int = 500
FT_TOKENS_EACH: int = 400
FT_EPOCHS: int = 3
FLOP_PER_TOKEN_FWD: float = 2.0 * TOTAL
FT_TOKENS: int = FT_EXAMPLES * FT_TOKENS_EACH * FT_EPOCHS
FT_FLOP: float = 6.0 * TOTAL * FT_TOKENS
PROMPT_FLOP_PER_CALL: float = PROMPT_TOKENS * FLOP_PER_TOKEN_FWD
CROSSOVER_CALLS: float = FT_FLOP / PROMPT_FLOP_PER_CALL


def report_prompt_cost() -> None:
    print('--- a longer prompt against a one-off fine-tune ---')
    print(f'forward pass per token      {FLOP_PER_TOKEN_FWD:.4g} FLOP  '
          f'({FLOP_PER_TOKEN_FWD / 1e9:.2f} GFLOP)')
    print(f'{PROMPT_TOKENS} extra prompt tokens    {PROMPT_FLOP_PER_CALL / 1e12:.2f} TFLOP per call')
    print(f'fine-tune on {FT_TOKENS:,} tokens  {FT_FLOP / 1e15:.2f} PFLOP once')
    print(f'crossover                   {CROSSOVER_CALLS:,.0f} calls')
    for n in (1_000, 10_000, 100_000):
        print(f'  after {n:>7,} calls the prompt has cost '
              f'{n * PROMPT_FLOP_PER_CALL / 1e15:8.2f} PFLOP '
              f'({n * PROMPT_FLOP_PER_CALL / FT_FLOP:6.2f} times the fine-tune)')


# --- low-rank adapter counts for one 4096 x 4096 weight matrix -----------

RANKS: list[int] = [1, 2, 4, 8, 16, 32, 64, 128]
FULL_MATRIX: int = D_MODEL * D_MODEL


def lora_count(rows: int, cols: int, r: int) -> int:
    return r * cols + rows * r


ATTACH: dict[str, int] = {
    'query and value': N_BLOCK * 2 * lora_count(D_MODEL, D_MODEL, LORA_R),
    'all four attention': N_BLOCK * 4 * lora_count(D_MODEL, D_MODEL, LORA_R),
    'attention and feed-forward':
        N_BLOCK * (4 * lora_count(D_MODEL, D_MODEL, LORA_R)
                   + lora_count(D_FF, D_MODEL, LORA_R)
                   + lora_count(D_FF, D_MODEL, LORA_R)
                   + lora_count(D_MODEL, D_FF, LORA_R)),
}


def report_lora() -> None:
    print('--- low-rank adapters on one 4096 x 4096 matrix ---')
    print(f'the matrix itself holds {FULL_MATRIX:,} numbers')
    for r in RANKS:
        c = lora_count(D_MODEL, D_MODEL, r)
        print(f'  rank {r:>3}: {c:>10,} numbers  ({100.0 * c / FULL_MATRIX:6.3f}% of the matrix)')
    print(f'the two shapes break even at rank {FULL_MATRIX // (2 * D_MODEL)}')
    print('--- where the adapters are attached, rank 8, whole model ---')
    for name, c in ATTACH.items():
        print(f'  {name:28s} {c:>12,} numbers  ({100.0 * c / TOTAL:7.4f}% of the model)')
    print(f'one feed-forward matrix is {D_MODEL} x {D_FF}, so a rank-{LORA_R} adapter on it '
          f'holds {lora_count(D_FF, D_MODEL, LORA_R):,} numbers')


# --- the alpha / r scaling factor, and folding the adapter back in -------

def lora_scaling() -> dict[str, object]:
    """How big the added update is as the rank grows, with three ways of scaling it."""
    rng = np.random.default_rng(3)
    ranks = [1, 2, 4, 8, 16, 32, 64, 128]
    alpha = 16.0
    rows = cols = 256          # a small stand-in matrix, so the sums stay quick
    x = rng.normal(0.0, 1.0, cols)
    x = x / np.linalg.norm(x)
    sigma = 0.05               # the typical size one training run leaves in A and B
    raw: list[float] = []
    for r in ranks:
        a = rng.normal(0.0, sigma, (r, cols))
        b = rng.normal(0.0, sigma, (rows, r))
        raw.append(float(np.linalg.norm(b @ (a @ x))))
    by_r = [v * alpha / r for v, r in zip(raw, ranks)]
    by_sqrt = [v * alpha / np.sqrt(r) for v, r in zip(raw, ranks)]
    # folding the adapter into the weights: the same answer, computed two ways
    w = rng.normal(0.0, 0.02, (rows, cols))
    a = rng.normal(0.0, sigma, (8, cols))
    b = rng.normal(0.0, sigma, (rows, 8))
    sc = alpha / 8.0
    side = w @ x + sc * (b @ (a @ x))
    folded = (w + sc * (b @ a)) @ x
    gap = float(np.max(np.abs(side - folded)))
    mac_w = D_MODEL * D_MODEL
    mac_side = 2 * LORA_R * D_MODEL
    print('--- the scaling factor and folding the adapter back in ---')
    print(f'alpha = {alpha:.0f}, and every number in A and B has typical size {sigma}')
    for r, u, br, bs in zip(ranks, raw, by_r, by_sqrt):
        print(f'  rank {r:>3}: no scaling {u:.4f}   alpha/r {br:.4f}   '
              f'alpha/sqrt(r) {bs:.4f}')
    print(f'  from rank 1 to rank 128 the unscaled update grows '
          f'{raw[-1] / raw[0]:.2f} times, the alpha/r one changes by '
          f'{by_r[-1] / by_r[0]:.3f} times and the alpha/sqrt(r) one by '
          f'{by_sqrt[-1] / by_sqrt[0]:.3f} times')
    print(f'  largest difference between a separate side path and a folded-in one: '
          f'{gap:.3g}')
    print(f'  multiply-adds per token for one {D_MODEL}x{D_MODEL} matrix: {mac_w:,} alone, '
          f'{mac_w + mac_side:,} with a separate rank-{LORA_R} side path '
          f'(+{100.0 * mac_side / mac_w:.2f}%), {mac_w:,} once folded in')
    return {'ranks': ranks, 'raw': raw, 'by_r': by_r, 'by_sqrt': by_sqrt,
            'gap': gap, 'mac_w': mac_w, 'mac_side': mac_side, 'alpha': alpha,
            'sigma': sigma}


# --- bits per weight once the scales are counted -------------------------

GROUPS: list[int] = [32, 64, 128, 256]
SCALE_BITS: int = 16


def bits_per_weight(bits: int, group: int) -> float:
    return bits + SCALE_BITS / group


def report_qlora() -> None:
    print('--- 4-bit base weights with grouped scales ---')
    for g in GROUPS:
        bpw = bits_per_weight(4, g)
        by = TOTAL * bpw / 8
        print(f'  group of {g:>3} weights: {bpw:.3f} bits per weight -> {_gib(by):.3f} GiB '
              f'for the whole model')
    bpw = bits_per_weight(4, 64)
    base = TOTAL * bpw / 8
    adapter = LORA_QV * B_TRAIN
    print(f'  a 4-bit base with groups of 64 plus rank-{LORA_R} adapters: '
          f'{_gib(base):.3f} + {_gib(adapter):.3f} = {_gib(base + adapter):.3f} GiB')
    print(f'  the same base in bfloat16 would be {_gib(TOTAL * 2):.3f} GiB')


# --- what has to fit on a robot's own computer ---------------------------

PRECISIONS: list[tuple[str, float]] = [
    ('float32', 32.0), ('bfloat16', 16.0), ('int8', 8.0 + SCALE_BITS / 64),
    ('int4', 4.0 + SCALE_BITS / 64)]
BANDWIDTH_GBS: float = 100.0        # a stated assumption: 100 GB a second
ACCEL_TFLOPS: float = 20.0          # a stated assumption: 20 TFLOP a second
ROBOT_GIB: float = 8.0              # a stated assumption: 8 GiB shared memory


def report_fit() -> None:
    print('--- what has to fit on the robot ---')
    for name, bpw in PRECISIONS:
        by = TOTAL * bpw / 8
        sec = by / (BANDWIDTH_GBS * 1e9)
        print(f'  {name:9s} {bpw:6.2f} bits/weight  {_gib(by):7.3f} GiB  '
              f'reading every weight once at {BANDWIDTH_GBS:.0f} GB/s takes {1e3 * sec:7.1f} ms '
              f'-> at most {1.0 / sec:6.2f} tokens a second')
    for hz in (5, 10, 30):
        budget = 1.0 / hz
        flop = budget * ACCEL_TFLOPS * 1e12
        print(f'  a {hz:>2} Hz control loop leaves {1e3 * budget:5.1f} ms, which at '
              f'{ACCEL_TFLOPS:.0f} TFLOP/s is {flop / 1e9:7.1f} GFLOP, or '
              f'{flop / FLOP_PER_TOKEN_FWD:5.1f} tokens of this model')


# ==========================================================================
# PART 2.  The simulated six-class problem and the small network.
# ==========================================================================

FEAT: int = 12               # the twelve readings the sensor gives
N_CLASS: int = 6             # six objects the robot has to tell apart
SPREAD: float = 1.0          # how widely one object's readings scatter
NEW_CLASSES: tuple[int, int] = (4, 5)
CLIP: float = 4.0            # gradient clipping, to keep these small runs stable


def _blobs(means: Arr, classes: list[int], per_class: int, rng: np.random.Generator,
           shift: Arr | None = None, spread: float = SPREAD) -> tuple[Arr, Ints]:
    """Draw readings for the given classes: a cloud of points around each class mean."""
    xs: list[Arr] = []
    ys: list[int] = []
    for c in classes:
        mu = means[c] + (shift if shift is not None else 0.0)
        xs.append(rng.normal(mu, spread, (per_class, FEAT)))
        ys += [c] * per_class
    return np.vstack(xs), np.array(ys)


def _clip(dw: list[Arr], db: list[Arr]) -> None:
    total = np.sqrt(sum(float(np.sum(g ** 2)) for g in dw)
                    + sum(float(np.sum(g ** 2)) for g in db))
    if total > CLIP:
        f = CLIP / total
        for g in dw:
            g *= f
        for g in db:
            g *= f


def _fwd(ws: list[Arr], bs: list[Arr], x: Arr) -> list[Arr]:
    acts: list[Arr] = [x]
    for i in range(len(ws)):
        z = acts[-1] @ ws[i] + bs[i]
        acts.append(np.maximum(z, 0.0) if i < len(ws) - 1 else z)
    return acts


def _ce_grad(logits: Arr, y: Ints) -> Arr:
    p = _softmax(logits)
    g = p.copy()
    g[np.arange(len(y)), y] -= 1.0
    return g / len(y)


def _back(ws: list[Arr], acts: list[Arr], g: Arr) -> tuple[list[Arr], list[Arr]]:
    dw: list[Arr] = [np.zeros_like(w) for w in ws]
    db: list[Arr] = [np.zeros(w.shape[1]) for w in ws]
    for i in range(len(ws) - 1, -1, -1):
        dw[i] = acts[i].T @ g
        db[i] = g.sum(axis=0)
        if i > 0:
            g = (g @ ws[i].T) * (acts[i] > 0)
    return dw, db


def accuracy(ws: list[Arr], bs: list[Arr], x: Arr, y: Ints) -> float:
    return float(np.mean(np.argmax(_fwd(ws, bs, x)[-1], axis=1) == y))


def new_net(sizes: list[int], rng: np.random.Generator) -> tuple[list[Arr], list[Arr]]:
    ws = [rng.normal(0.0, np.sqrt(2.0 / a), (a, b)) for a, b in zip(sizes[:-1], sizes[1:])]
    bs = [np.zeros(b) for b in sizes[1:]]
    return ws, bs


def train_full(ws: list[Arr], bs: list[Arr], x: Arr, y: Ints, steps: int, lr: float,
               rng: np.random.Generator, batch: int = 64, trainable: list[int] | None = None,
               mix: tuple[Arr, Ints, float] | None = None,
               track: list[tuple[Arr, Ints]] | None = None
               ) -> tuple[list[Arr], list[Arr], list[list[float]]]:
    """Plain mini-batch gradient descent with momentum on the layers in `trainable`."""
    ws = [w.copy() for w in ws]
    bs = [b.copy() for b in bs]
    if trainable is None:
        trainable = list(range(len(ws)))
    vw = [np.zeros_like(w) for w in ws]
    vb = [np.zeros_like(b) for b in bs]
    hist: list[list[float]] = [[] for _ in (track or [])]
    for step in range(steps):
        if track is not None:
            for k, (xt, yt) in enumerate(track):
                hist[k].append(accuracy(ws, bs, xt, yt))
        idx = rng.integers(0, len(y), min(batch, len(y)))
        xb, yb = x[idx], y[idx]
        if mix is not None:
            xo, yo, frac = mix
            k = max(1, int(round(frac * batch)))
            j = rng.integers(0, len(yo), k)
            xb = np.vstack([xb, xo[j]])
            yb = np.concatenate([yb, yo[j]])
        acts = _fwd(ws, bs, xb)
        dw, db = _back(ws, acts, _ce_grad(acts[-1], yb))
        _clip(dw, db)
        for i in trainable:
            vw[i] = 0.9 * vw[i] + dw[i]
            vb[i] = 0.9 * vb[i] + db[i]
            ws[i] -= lr * vw[i]
            bs[i] -= lr * vb[i]
    if track is not None:
        for k, (xt, yt) in enumerate(track):
            hist[k].append(accuracy(ws, bs, xt, yt))
    return ws, bs, hist


def train_lowrank(ws: list[Arr], bs: list[Arr], x: Arr, y: Ints, rank: int, steps: int,
                  lr: float, rng: np.random.Generator, batch: int = 64,
                  alpha: float | None = None, mix: tuple[Arr, Ints, float] | None = None,
                  track: list[tuple[Arr, Ints]] | None = None
                  ) -> tuple[list[Arr], list[Arr], list[list[float]], int]:
    """Train only a rank-`rank` side path on every weight matrix; the base stays frozen."""
    scale = (alpha if alpha is not None else float(rank)) / rank
    a = [rng.normal(0.0, 1.0 / np.sqrt(w.shape[0]), (w.shape[0], rank)) for w in ws]
    b = [np.zeros((rank, w.shape[1])) for w in ws]
    bias = [bb.copy() for bb in bs]
    va = [np.zeros_like(m) for m in a]
    vb = [np.zeros_like(m) for m in b]
    vbias = [np.zeros_like(m) for m in bias]
    n_train = sum(m.size for m in a) + sum(m.size for m in b) + sum(m.size for m in bias)
    hist: list[list[float]] = [[] for _ in (track or [])]

    def eff() -> list[Arr]:
        return [ws[i] + scale * (a[i] @ b[i]) for i in range(len(ws))]

    for step in range(steps):
        if track is not None:
            we = eff()
            for k, (xt, yt) in enumerate(track):
                hist[k].append(accuracy(we, bias, xt, yt))
        idx = rng.integers(0, len(y), min(batch, len(y)))
        xb, yb = x[idx], y[idx]
        if mix is not None:
            xo, yo, frac = mix
            k = max(1, int(round(frac * batch)))
            j = rng.integers(0, len(yo), k)
            xb = np.vstack([xb, xo[j]])
            yb = np.concatenate([yb, yo[j]])
        we = eff()
        acts = _fwd(we, bias, xb)
        dw, db = _back(we, acts, _ce_grad(acts[-1], yb))
        _clip(dw, db)
        for i in range(len(ws)):
            ga = scale * (dw[i] @ b[i].T)
            gb = scale * (a[i].T @ dw[i])
            va[i] = 0.9 * va[i] + ga
            vb[i] = 0.9 * vb[i] + gb
            vbias[i] = 0.9 * vbias[i] + db[i]
            a[i] -= lr * va[i]
            b[i] -= lr * vb[i]
            bias[i] -= lr * vbias[i]
    we = eff()
    if track is not None:
        for k, (xt, yt) in enumerate(track):
            hist[k].append(accuracy(we, bias, xt, yt))
    return we, bias, hist, n_train


# --------------------------------------------------------------------------
# quantisation, used by both pages
# --------------------------------------------------------------------------

def quantise(w: Arr, bits: int, mode: str = 'per-tensor', group: int | None = None,
             clip: float | None = None) -> tuple[Arr, Ints, Arr]:
    """Symmetric quantisation to `bits` bits. Returns dequantised weights, integers, scales."""
    qmax = 2 ** (bits - 1) - 1
    if mode == 'per-tensor':
        amax = np.array([[np.abs(w).max() if clip is None
                          else np.quantile(np.abs(w), clip)]])
        scale = amax / qmax
        q = np.clip(np.rint(w / scale), -qmax, qmax).astype(np.int64)
        return q * scale, q, scale
    if mode == 'per-channel':
        amax = (np.abs(w).max(axis=0, keepdims=True) if clip is None
                else np.quantile(np.abs(w), clip, axis=0, keepdims=True))
        scale = np.maximum(amax, 1e-12) / qmax
        q = np.clip(np.rint(w / scale), -qmax, qmax).astype(np.int64)
        return q * scale, q, scale
    # grouped: groups of `group` weights down each column
    assert group is not None
    rows, cols = w.shape
    pad = (-rows) % group
    wp = np.vstack([w, np.zeros((pad, cols))]) if pad else w
    blocks = wp.reshape(-1, group, cols)
    amax = np.abs(blocks).max(axis=1, keepdims=True)
    scale = np.maximum(amax, 1e-12) / qmax
    q = np.clip(np.rint(blocks / scale), -qmax, qmax).astype(np.int64)
    deq = (q * scale).reshape(-1, cols)[:rows]
    return deq, q.reshape(-1, cols)[:rows], scale.reshape(-1, cols)


def rms(a: Arr) -> float:
    return float(np.sqrt(np.mean(a ** 2)))


def quantise_net(ws: list[Arr], bits: int, mode: str = 'per-channel',
                 group: int | None = None, clip: float | None = None) -> list[Arr]:
    return [quantise(w, bits, mode, group, clip)[0] for w in ws]


def train_qat(ws: list[Arr], bs: list[Arr], x: Arr, y: Ints, bits: int, steps: int,
              lr: float, rng: np.random.Generator, batch: int = 64) -> list[Arr]:
    """Quantisation-aware training: the forward pass uses quantised weights, the
    update is applied to the stored full-precision weights (straight-through)."""
    ws = [w.copy() for w in ws]
    bs = [b.copy() for b in bs]
    vw = [np.zeros_like(w) for w in ws]
    vb = [np.zeros_like(b) for b in bs]
    for _ in range(steps):
        idx = rng.integers(0, len(y), min(batch, len(y)))
        wq = quantise_net(ws, bits, 'per-channel')
        acts = _fwd(wq, bs, x[idx])
        dw, db = _back(wq, acts, _ce_grad(acts[-1], y[idx]))
        _clip(dw, db)
        for i in range(len(ws)):
            vw[i] = 0.9 * vw[i] + dw[i]
            vb[i] = 0.9 * vb[i] + db[i]
            ws[i] -= lr * vw[i]
            bs[i] -= lr * vb[i]
    return ws


# --------------------------------------------------------------------------
# everything the experiments share, worked out once
# --------------------------------------------------------------------------

class Sim:
    """The simulated task, the pretrained network, and every experiment on it."""

    def __init__(self) -> None:
        rng = np.random.default_rng(11)
        self.rng = rng
        self.means = rng.normal(0.0, 1.25, (N_CLASS, FEAT))
        all_classes = list(range(N_CLASS))
        self.x_old, self.y_old = _blobs(self.means, all_classes, 320, rng)
        self.x_old_t, self.y_old_t = _blobs(self.means, all_classes, 320, rng)
        # The new job is narrow and harder: it only ever shows two of the six
        # objects, their readings have moved to a new part of the space, and the
        # two clouds now sit close enough together to overlap.
        self.step = np.zeros(FEAT)
        self.step[:4] = np.array([1.1, -1.05, 0.9, -0.75])
        self.gap = np.zeros(FEAT)
        self.gap[4:8] = np.array([1.05, 0.95, -1.0, 0.85])
        self.x_new, self.y_new = self.new_job(1.0, 320, rng)
        self.x_new_t, self.y_new_t = self.new_job(1.0, 320, rng)
        self.sizes = [FEAT, 32, 32, N_CLASS]
        w0, b0 = new_net(self.sizes, rng)
        self.w, self.b, _ = train_full(w0, b0, self.x_old, self.y_old, 1400, 0.08, rng, batch=96)
        self.n_param = sum(w.size for w in self.w) + sum(b.size for b in self.b)
        self.acc_old = accuracy(self.w, self.b, self.x_old_t, self.y_old_t)
        self.acc_new_before = accuracy(self.w, self.b, self.x_new_t, self.y_new_t)
        self.ceiling = self.bayes_new()

    def new_job(self, distance: float, per_class: int, rng: np.random.Generator,
                spread: float = SPREAD, offset: Arr | None = None
                ) -> tuple[Arr, Ints]:
        """Readings for the narrow new job, `distance` steps away from the old job."""
        base = self.means[NEW_CLASSES[0]] + distance * self.step
        if offset is not None:
            base = base + offset
        mus = np.vstack([base, base + self.gap])
        xs = [rng.normal(mu, spread, (per_class, FEAT)) for mu in mus]
        ys = np.array([NEW_CLASSES[0]] * per_class + [NEW_CLASSES[1]] * per_class)
        return np.vstack(xs), ys

    def bayes_new(self) -> float:
        """The best accuracy anything could reach on the new job's two clouds."""
        d = float(np.linalg.norm(self.gap)) / SPREAD
        from math import erf, sqrt
        return 0.5 * (1.0 + erf((d / 2.0) / sqrt(2.0)))

    def report(self) -> None:
        print('--- the simulated six-class task and the pretrained network ---')
        print(f'network {self.sizes}, {self.n_param:,} parameters')
        print(f'training set {len(self.y_old):,} examples, test set {len(self.y_old_t):,}')
        print(f'one step away is a distance of {float(np.linalg.norm(self.step)):.3f} '
              f'in reading space; the two new clouds are '
              f'{float(np.linalg.norm(self.gap)):.3f} apart')
        print(f'accuracy on the old six-class test set:        {self.acc_old:.3f}')
        print(f'accuracy on the new two-way job before tuning: {self.acc_new_before:.3f}')
        print(f'best accuracy anything could reach on the new job: {self.ceiling:.3f}')


SIM: Sim | None = None


def sim() -> Sim:
    global SIM
    if SIM is None:
        SIM = Sim()
        SIM.report()
    return SIM


def train_distil(sizes: list[int], x: Arr, y: Ints, teacher_logits: Arr, temperature: float,
                 soft_weight: float, steps: int, lr: float, rng: np.random.Generator,
                 batch: int = 32) -> tuple[list[Arr], list[Arr]]:
    """Train a student on hard labels, on the teacher's soft targets, or on a mix."""
    ws, bs = new_net(sizes, rng)
    vw = [np.zeros_like(w) for w in ws]
    vb = [np.zeros_like(b) for b in bs]
    q = _softmax(teacher_logits / temperature)
    for _ in range(steps):
        idx = rng.integers(0, len(y), min(batch, len(y)))
        acts = _fwd(ws, bs, x[idx])
        g_hard = _ce_grad(acts[-1], y[idx])
        p_soft = _softmax(acts[-1] / temperature)
        g_soft = (p_soft - q[idx]) / (temperature * len(idx))
        g = (1.0 - soft_weight) * g_hard + soft_weight * (temperature ** 2) * g_soft
        dw, db = _back(ws, acts, g)
        _clip(dw, db)
        for i in range(len(ws)):
            vw[i] = 0.9 * vw[i] + dw[i]
            vb[i] = 0.9 * vb[i] + db[i]
            ws[i] -= lr * vw[i]
            bs[i] -= lr * vb[i]
    return ws, bs


def macs(sizes: list[int]) -> int:
    return sum(a * b for a, b in zip(sizes[:-1], sizes[1:]))


class Big:
    """A larger network on the same task, used for the squeezing experiments."""

    def __init__(self, s: Sim) -> None:
        rng = np.random.default_rng(23)
        self.rng = rng
        self.sizes = [FEAT, 48, 48, N_CLASS]
        w0, b0 = new_net(self.sizes, rng)
        self.w, self.b, _ = train_full(w0, b0, s.x_old, s.y_old, 2200, 0.08, rng, batch=96)
        self.n_param = sum(w.size for w in self.w) + sum(b.size for b in self.b)
        self.macs = macs(self.sizes)
        self.acc = accuracy(self.w, self.b, s.x_old_t, s.y_old_t)
        self.logits = _fwd(self.w, self.b, s.x_old)[-1]

    def report(self) -> None:
        print('--- the larger network used for squeezing ---')
        print(f'network {self.sizes}, {self.n_param:,} parameters, '
              f'{self.macs:,} multiply-adds per example')
        print(f'accuracy on the six-class test set: {self.acc:.3f}')


BIG: Big | None = None


def big() -> Big:
    global BIG
    if BIG is None:
        BIG = Big(sim())
        BIG.report()
    return BIG


# ==========================================================================
# PART 3.  The experiments on the simulated task.
# ==========================================================================

CURVE_N: list[int] = [4, 8, 16, 32, 64, 128, 256, 512]
REPEATS: int = 15
FT_STEPS: int = 300
FT_LR: float = 0.05


def _finetune(s: Sim, kind: str, xs: Arr, ys: Ints, rng: np.random.Generator,
              base: list[Arr] | None = None) -> tuple[list[Arr], list[Arr], int]:
    """One fine-tune of the pretrained network on (xs, ys), by one of four methods."""
    w = base if base is not None else s.w
    if kind == 'head':
        wn, bn, _ = train_full(w, s.b, xs, ys, FT_STEPS, FT_LR, rng, batch=32,
                               trainable=[len(w) - 1])
        return wn, bn, w[-1].size + s.b[-1].size
    if kind == 'lora2':
        wn, bn, _, n = train_lowrank(w, s.b, xs, ys, 2, FT_STEPS, FT_LR, rng, batch=32)
        return wn, bn, n
    if kind == 'lora8':
        wn, bn, _, n = train_lowrank(w, s.b, xs, ys, 8, FT_STEPS, FT_LR, rng, batch=32)
        return wn, bn, n
    wn, bn, _ = train_full(w, s.b, xs, ys, FT_STEPS, FT_LR, rng, batch=32)
    return wn, bn, s.n_param


_CACHE: dict[str, object] = {}


def exp_curves() -> dict[str, list[float]]:
    """New-job test accuracy against the number of new-job examples, four ways."""
    if 'curves' in _CACHE:
        return _CACHE['curves']          # type: ignore[return-value]
    s = sim()
    out: dict[str, list[float]] = {k: [] for k in ('head', 'lora2', 'full')}
    counts: dict[str, int] = {}
    for n in CURVE_N:
        for kind in out:
            vals: list[float] = []
            for rep in range(REPEATS):
                rng = np.random.default_rng(500 + rep)
                xs, ys = s.new_job(1.0, n // 2, rng)
                w, b, ntr = _finetune(s, kind, xs, ys, rng)
                vals.append(accuracy(w, b, s.x_new_t, s.y_new_t))
                counts[kind] = ntr
            out[kind].append(float(np.mean(vals)))
    print('--- new-job accuracy against the number of examples '
          f'(mean of {REPEATS} runs) ---')
    print('examples        ' + ' '.join(f'{n:>6}' for n in CURVE_N))
    for kind, vals in out.items():
        print(f'{kind:8s} ({counts[kind]:>5,}) ' + ' '.join(f'{v:6.3f}' for v in vals))
    print(f'before any tuning the pretrained network scores {s.acc_new_before:.3f}, '
          f'and nothing can beat {s.ceiling:.3f}')
    out['_counts'] = [counts['head'], counts['lora2'], counts['full']]   # type: ignore[assignment]
    _CACHE['curves'] = out
    return out


def exp_forgetting() -> dict[str, object]:
    """What a hard fine-tune on the narrow new job does to the old six-way job."""
    if 'forget' in _CACHE:
        return _CACHE['forget']          # type: ignore[return-value]
    s = sim()
    rng = np.random.default_rng(31)
    track = [(s.x_old_t, s.y_old_t), (s.x_new_t, s.y_new_t)]
    w_hard, b_hard, hist = train_full(s.w, s.b, s.x_new, s.y_new, 300, 0.15, rng,
                                      batch=64, track=track)
    recipes: list[tuple[str, float, float]] = []
    r = np.random.default_rng(32)
    w, b, _ = train_full(s.w, s.b, s.x_new, s.y_new, 300, 0.15, r, batch=64)
    recipes.append(('full, 300 steps,\nlr 0.15', accuracy(w, b, s.x_old_t, s.y_old_t),
                    accuracy(w, b, s.x_new_t, s.y_new_t)))
    w, b, _ = train_full(s.w, s.b, s.x_new, s.y_new, 10, 0.15, r, batch=64)
    recipes.append(('full, 10 steps,\nlr 0.15', accuracy(w, b, s.x_old_t, s.y_old_t),
                    accuracy(w, b, s.x_new_t, s.y_new_t)))
    w, b, _ = train_full(s.w, s.b, s.x_new, s.y_new, 300, 0.012, r, batch=64)
    recipes.append(('full, 300 steps,\nlr 0.012', accuracy(w, b, s.x_old_t, s.y_old_t),
                    accuracy(w, b, s.x_new_t, s.y_new_t)))
    w, b, _ = train_full(s.w, s.b, s.x_new, s.y_new, 300, 0.15, r, batch=64,
                         mix=(s.x_old, s.y_old, 0.25))
    recipes.append(('full, 300 steps, lr 0.15,\n25% old data mixed in',
                    accuracy(w, b, s.x_old_t, s.y_old_t),
                    accuracy(w, b, s.x_new_t, s.y_new_t)))
    w, b, _, _ = train_lowrank(s.w, s.b, s.x_new, s.y_new, 2, 300, 0.012, r, batch=64)
    recipes.append(('rank-2 adapter,\n300 steps, lr 0.012',
                    accuracy(w, b, s.x_old_t, s.y_old_t),
                    accuracy(w, b, s.x_new_t, s.y_new_t)))
    recipes.append(('the same adapter\nswitched off again',
                    accuracy(s.w, s.b, s.x_old_t, s.y_old_t),
                    accuracy(s.w, s.b, s.x_new_t, s.y_new_t)))
    # the whole frontier: every learning rate against every number of steps
    lrs = [0.004, 0.012, 0.04, 0.15, 0.4]
    step_list = [25, 50, 100, 200, 400]
    front: list[tuple[float, int, float, float]] = []
    for lr in lrs:
        for st in step_list:
            r2 = np.random.default_rng(44)
            w, b, _ = train_full(s.w, s.b, s.x_new, s.y_new, st, lr, r2, batch=64)
            front.append((lr, st, accuracy(w, b, s.x_old_t, s.y_old_t),
                          accuracy(w, b, s.x_new_t, s.y_new_t)))
    print('--- forgetting ---')
    print(f'before the fine-tune: old {s.acc_old:.3f}, new {s.acc_new_before:.3f}')
    for i in (0, 5, 10, 25, 50, 100, 200, 300):
        print(f'  after {i:>3} steps of a hard full fine-tune: '
              f'old {hist[0][i]:.3f}, new {hist[1][i]:.3f}')
    for name, old, new in recipes:
        print(f'  {name.replace(chr(10), " "):32s} old {old:.3f}  new {new:.3f}')
    out = {'hist': hist, 'recipes': recipes, 'front': front,
           'w_hard': w_hard, 'b_hard': b_hard}
    _CACHE['forget'] = out
    return out


def exp_mix_fraction() -> list[tuple[float, float, float]]:
    """How much of the old data has to be mixed back in."""
    if 'mixfrac' in _CACHE:
        return _CACHE['mixfrac']         # type: ignore[return-value]
    s = sim()
    out: list[tuple[float, float, float]] = []
    for frac in (0.0, 0.05, 0.10, 0.25, 0.50, 1.0):
        r = np.random.default_rng(55)
        mix = None if frac == 0.0 else (s.x_old, s.y_old, frac)
        w, b, _ = train_full(s.w, s.b, s.x_new, s.y_new, 300, 0.15, r, batch=64, mix=mix)
        out.append((frac, accuracy(w, b, s.x_old_t, s.y_old_t),
                    accuracy(w, b, s.x_new_t, s.y_new_t)))
    print('--- mixing some of the old data back in ---')
    for frac, old, new in out:
        print(f'  {100 * frac:5.0f}% old data in each batch: old {old:.3f}, new {new:.3f}')
    _CACHE['mixfrac'] = out
    return out


def exp_distance() -> dict[str, object]:
    """Three new jobs at increasing distance from the old one, and the data each needs."""
    if 'dist' in _CACHE:
        return _CACHE['dist']            # type: ignore[return-value]
    s = sim()
    step = s.step

    def moved(dist: float, per: int, rng: np.random.Generator) -> tuple[Arr, Ints]:
        mus = [s.means[4] + dist * step, s.means[5] + dist * step]
        xs = [rng.normal(mu, SPREAD, (per, FEAT)) for mu in mus]
        return np.vstack(xs), np.array([4] * per + [5] * per)

    gap_easy = float(np.linalg.norm(s.means[4] - s.means[5])) / SPREAD
    from math import erf, sqrt
    ceil_easy = 0.5 * (1.0 + erf((gap_easy / 2.0) / sqrt(2.0)))
    jobs: list[tuple[str, float, object]] = [
        ('A: same two objects,\none step away', ceil_easy, 1.0),
        ('B: same two objects,\nfour steps away', ceil_easy, 4.0),
        ('C: a finer distinction\nthe model never made', s.ceiling, None),
    ]
    ns = [4, 8, 16, 32, 64, 128, 256, 512]
    curves: list[list[float]] = []
    befores: list[float] = []
    needed: list[int | None] = []
    for name, ceiling, dist in jobs:
        rng = np.random.default_rng(7)
        if dist is None:
            xt, yt = s.new_job(1.0, 400, rng)
        else:
            xt, yt = moved(float(dist), 400, rng)
        befores.append(accuracy(s.w, s.b, xt, yt))
        row: list[float] = []
        for n in ns:
            vals: list[float] = []
            for rep in range(3):
                r2 = np.random.default_rng(900 + rep)
                if dist is None:
                    xs, ys = s.new_job(1.0, n // 2, r2)
                else:
                    xs, ys = moved(float(dist), n // 2, r2)
                w, b, _ = _finetune(s, 'full', xs, ys, r2)
                vals.append(accuracy(w, b, xt, yt))
            row.append(float(np.mean(vals)))
        curves.append(row)
        target = ceiling - 0.03
        hit = [n for n, v in zip(ns, row) if v >= target]
        needed.append(hit[0] if hit else None)
    print('--- how far the new job is from the old one ---')
    for (name, ceiling, _d), before, row, nd in zip(jobs, befores, curves, needed):
        print(f'  {name.replace(chr(10), " ")}')
        print(f'     ceiling {ceiling:.3f}, before tuning {before:.3f}')
        print('     ' + ' '.join(f'n={n}:{v:.3f}' for n, v in zip(ns, row)))
        print(f'     examples to come within 0.03 of the ceiling: '
              f'{nd if nd is not None else "more than " + str(ns[-1])}')
    out = {'jobs': [j[0] for j in jobs], 'ceilings': [j[1] for j in jobs],
           'ns': ns, 'curves': curves, 'befores': befores, 'needed': needed}
    _CACHE['dist'] = out
    return out


def exp_narrow() -> dict[str, float]:
    """64 examples from one corner of the new job, against 64 spread over all of it."""
    if 'narrow' in _CACHE:
        return _CACHE['narrow']          # type: ignore[return-value]
    s = sim()
    res: dict[str, float] = {}
    for label, spread in (('narrow', 0.3), ('spread', SPREAD)):
        vals_new: list[float] = []
        vals_train: list[float] = []
        for rep in range(5):
            rng = np.random.default_rng(770 + rep)
            off = None
            if label == 'narrow':
                off = np.zeros(FEAT)
                off[:4] = np.array([0.45, 0.4, -0.4, 0.35])
            xs, ys = s.new_job(1.0, 32, rng, spread=spread, offset=off)
            w, b, _ = _finetune(s, 'full', xs, ys, rng)
            vals_new.append(accuracy(w, b, s.x_new_t, s.y_new_t))
            vals_train.append(accuracy(w, b, xs, ys))
        res[label + '_test'] = float(np.mean(vals_new))
        res[label + '_train'] = float(np.mean(vals_train))
    print('--- 64 examples from one corner against 64 spread over the whole job ---')
    for label in ('narrow', 'spread'):
        print(f'  {label:7s} examples: on its own examples {res[label + "_train"]:.3f}, '
              f'on the whole new job {res[label + "_test"]:.3f}')
    _CACHE['narrow'] = res
    return res


def exp_variation() -> dict[str, object]:
    """How much data the new job needs as the job itself gets more varied."""
    if 'variation' in _CACHE:
        return _CACHE['variation']       # type: ignore[return-value]
    from math import erf, sqrt
    s = sim()
    gap = float(np.linalg.norm(s.gap))
    spreads = [0.5, 0.75, 1.0, 1.3, 1.6]
    ns = [4, 8, 16, 32, 64, 128, 256, 512]
    ceils: list[float] = []
    curves: list[list[float]] = []
    needed: list[int | None] = []
    for sp in spreads:
        ceil = 0.5 * (1.0 + erf((gap / sp / 2.0) / sqrt(2.0)))
        ceils.append(ceil)
        rng = np.random.default_rng(7)
        xt, yt = s.new_job(1.0, 400, rng, spread=sp)
        row: list[float] = []
        for n in ns:
            vals: list[float] = []
            for rep in range(3):
                r2 = np.random.default_rng(900 + rep)
                xs, ys = s.new_job(1.0, n // 2, r2, spread=sp)
                w, b, _ = _finetune(s, 'full', xs, ys, r2)
                vals.append(accuracy(w, b, xt, yt))
            row.append(float(np.mean(vals)))
        curves.append(row)
        hit = [n for n, v in zip(ns, row) if v >= ceil - 0.03]
        needed.append(hit[0] if hit else None)
    print('--- how varied the new job is, and what that costs in examples ---')
    for sp, ceil, nd, row in zip(spreads, ceils, needed, curves):
        print(f'  scatter {sp:.2f}: ceiling {ceil:.3f}, examples needed '
              f'{nd if nd is not None else "more than 512"}   '
              + ' '.join(f'{v:.3f}' for v in row))
    out = {'spreads': spreads, 'ceilings': ceils, 'ns': ns,
           'curves': curves, 'needed': needed}
    _CACHE['variation'] = out
    return out


def exp_quant_adapter() -> dict[str, float]:
    """A frozen 4-bit base with a small adapter on top, against the other choices."""
    if 'qadapt' in _CACHE:
        return _CACHE['qadapt']          # type: ignore[return-value]
    s = sim()
    out: dict[str, float] = {}
    w4 = quantise_net(s.w, 4, 'per-channel')
    w8 = quantise_net(s.w, 8, 'per-channel')
    out['float base, no adapter'] = accuracy(s.w, s.b, s.x_new_t, s.y_new_t)
    out['4-bit base, no adapter'] = accuracy(w4, s.b, s.x_new_t, s.y_new_t)
    out['old job, float base'] = accuracy(s.w, s.b, s.x_old_t, s.y_old_t)
    out['old job, 4-bit base'] = accuracy(w4, s.b, s.x_old_t, s.y_old_t)
    out['old job, 8-bit base'] = accuracy(w8, s.b, s.x_old_t, s.y_old_t)
    for label, base in (('float base + rank-2 adapter', s.w),
                        ('8-bit base + rank-2 adapter', w8),
                        ('4-bit base + rank-2 adapter', w4)):
        vals: list[float] = []
        for rep in range(5):
            rng = np.random.default_rng(640 + rep)
            xs, ys = s.new_job(1.0, 64, rng)
            w, b, _ = _finetune(s, 'lora2', xs, ys, rng, base=base)
            vals.append(accuracy(w, b, s.x_new_t, s.y_new_t))
        out[label] = float(np.mean(vals))
    print('--- an adapter on a squeezed base ---')
    for k, v in out.items():
        print(f'  {k:32s} {v:.3f}')
    _CACHE['qadapt'] = out
    return out


# --------------------------------------------------------------------------
# page 4: making the model smaller and faster
# --------------------------------------------------------------------------

def exp_weight_row() -> dict[str, object]:
    """One real column of trained weights, turned into 8-bit and 4-bit integers."""
    if 'wrow' in _CACHE:
        return _CACHE['wrow']            # type: ignore[return-value]
    b = big()
    w = b.w[1][:, 0].copy()              # 48 trained weights, one output channel
    res: dict[str, object] = {'w': w}
    print('--- one real column of 48 trained weights ---')
    print(f'smallest {w.min():+.5f}, largest {w.max():+.5f}, '
          f'largest size {np.abs(w).max():.5f}')
    for bits in (8, 4):
        qmax = 2 ** (bits - 1) - 1
        scale = float(np.abs(w).max()) / qmax
        q = np.clip(np.rint(w / scale), -qmax, qmax).astype(int)
        deq = q * scale
        err = deq - w
        res[f'q{bits}'] = q
        res[f'deq{bits}'] = deq
        res[f'scale{bits}'] = scale
        res[f'rms{bits}'] = rms(err)
        res[f'max{bits}'] = float(np.abs(err).max())
        print(f'  {bits} bits: integers run from {-qmax} to {qmax}, '
              f'step {scale:.6f}, worst error {np.abs(err).max():.6f}, '
              f'root-mean-square error {rms(err):.6f}')
        print(f'    first eight weights   ' + ' '.join(f'{v:+.4f}' for v in w[:8]))
        print(f'    first eight integers  ' + ' '.join(f'{v:+5d}' for v in q[:8]))
        print(f'    read back as          ' + ' '.join(f'{v:+.4f}' for v in deq[:8]))
    bit_list = [2, 3, 4, 5, 6, 8, 10]
    rms_list: list[float] = []
    for bits in bit_list:
        qmax = 2 ** (bits - 1) - 1
        scale = float(np.abs(w).max()) / qmax
        q = np.clip(np.rint(w / scale), -qmax, qmax)
        rms_list.append(rms(q * scale - w))
    res['bit_list'] = bit_list
    res['rms_list'] = rms_list
    print('  root-mean-square error against the number of bits:')
    for bits, e in zip(bit_list, rms_list):
        print(f'    {bits:>2} bits: {e:.7f}')
    print(f'  going from 8 bits to 4 bits multiplies the error by '
          f'{rms_list[2] / rms_list[5]:.1f}')
    _CACHE['wrow'] = res
    return res


def exp_per_channel() -> dict[str, object]:
    """One scale for the whole matrix, one per output channel, or one per group."""
    if 'perchan' in _CACHE:
        return _CACHE['perchan']         # type: ignore[return-value]
    b = big()
    w = b.w[1].copy()                    # 48 x 48 trained weights
    loud = w.copy()
    loud[:, 7] *= 8.0                    # one channel with much larger weights
    res: dict[str, object] = {}
    print('--- one scale for everything, or one scale per channel ---')
    for label, mat in (('as trained', w), ('with one loud channel', loud)):
        line: dict[str, float] = {}
        for bits in (8, 4):
            for mode, group in (('per-tensor', None), ('per-channel', None),
                                ('grouped', 16)):
                deq, _q, _sc = quantise(mat, bits, mode, group)
                line[f'{mode}{bits}'] = rms(deq - mat) / rms(mat)
        res[label] = line
        print(f'  {label}: largest weight {np.abs(mat).max():.4f}, '
              f'typical weight {rms(mat):.4f}')
        for bits in (8, 4):
            print(f'    {bits} bits  '
                  + '  '.join(f'{m}: {100 * line[f"{m}{bits}"]:.3f}% error'
                              for m in ('per-tensor', 'per-channel', 'grouped')))
    rows, cols = w.shape
    res['overhead'] = {'per-tensor': 16.0 / w.size, 'per-channel': 16.0 / rows,
                       'grouped': 16.0 / 16}
    print('  extra bits per weight for the scales: '
          f'per-tensor {16.0 / w.size:.5f}, per-channel {16.0 / rows:.4f}, '
          f'groups of 16 {16.0 / 16:.2f}')
    res['w'] = w
    res['loud'] = loud
    _CACHE['perchan'] = res
    return res


def exp_ptq_qat() -> dict[str, object]:
    """Quantising a trained network, against training it with quantisation in mind."""
    if 'ptqqat' in _CACHE:
        return _CACHE['ptqqat']          # type: ignore[return-value]
    s = sim()
    b = big()
    bit_list = [8, 6, 5, 4, 3, 2]
    ptq: list[float] = []
    qat: list[float] = []
    for bits in bit_list:
        wq = quantise_net(b.w, bits, 'per-channel')
        ptq.append(accuracy(wq, b.b, s.x_old_t, s.y_old_t))
        rng = np.random.default_rng(300 + bits)
        wt = train_qat(b.w, b.b, s.x_old, s.y_old, bits, 600, 0.03, rng, batch=96)
        wtq = quantise_net(wt, bits, 'per-channel')
        qat.append(accuracy(wtq, b.b, s.x_old_t, s.y_old_t))
    modes: dict[str, list[float]] = {'per-tensor': [], 'per-channel': [], 'grouped': []}
    for bits in bit_list:
        for mode in modes:
            wq = quantise_net(b.w, bits, mode, 16 if mode == 'grouped' else None)
            modes[mode].append(accuracy(wq, b.b, s.x_old_t, s.y_old_t))
    clips: list[tuple[str, float]] = []
    for label, clip in (('largest weight', None), ('99.9th percentile', 0.999),
                        ('99th percentile', 0.99), ('95th percentile', 0.95)):
        wq = quantise_net(b.w, 4, 'per-channel', clip=clip)
        clips.append((label, accuracy(wq, b.b, s.x_old_t, s.y_old_t)))
    print('--- quantising after training, and training with it in mind ---')
    print(f'the float network scores {b.acc:.3f}')
    for bits, a, c in zip(bit_list, ptq, qat):
        print(f'  {bits:>2} bits: after training {a:.3f}, trained with it in mind {c:.3f}')
    for label, a in clips:
        print(f'  4 bits, scale set by the {label}: {a:.3f}')
    for mode, vals in modes.items():
        print(f'  {mode:12s} ' + ' '.join(f'{bb}b:{v:.3f}' for bb, v in zip(bit_list, vals)))
    out = {'bits': bit_list, 'ptq': ptq, 'qat': qat, 'clips': clips, 'float': b.acc,
           'modes': modes}
    _CACHE['ptqqat'] = out
    return out


def exp_distil() -> dict[str, object]:
    """A small student trained on hard labels, and on the teacher's whole answer."""
    if 'distil' in _CACHE:
        return _CACHE['distil']          # type: ignore[return-value]
    s = sim()
    t = big()
    student_sizes = [FEAT, 8, N_CLASS]
    n_student = sum(a * b + b for a, b in zip(student_sizes[:-1], student_sizes[1:]))
    # one worked example of a soft target: an example the teacher is unsure about
    top = _softmax(t.logits).max(axis=1)
    pick = int(np.argmin(np.abs(top - 0.70)))
    z = t.logits[pick]
    rows: dict[float, Arr] = {}
    for temp in (1.0, 2.0, 3.0, 5.0, 8.0):
        rows[temp] = _softmax(z / temp)
    ent = {temp: float(-np.sum(p * np.log2(p + 1e-12))) for temp, p in rows.items()}
    ns = [10, 20, 40, 80, 160, 320, 640]
    hard: list[float] = []
    soft: list[float] = []
    q8v: list[float] = []
    q4v: list[float] = []
    for n in ns:
        hv: list[float] = []
        sv: list[float] = []
        for rep in range(5):
            rng = np.random.default_rng(810 + rep)
            idx = rng.permutation(len(s.y_old))[:n]
            xs, ys, zl = s.x_old[idx], s.y_old[idx], t.logits[idx]
            w, b = train_distil(student_sizes, xs, ys, zl, 1.0, 0.0, 2000, 0.05, rng)
            hv.append(accuracy(w, b, s.x_old_t, s.y_old_t))
            w, b = train_distil(student_sizes, xs, ys, zl, 3.0, 0.9, 2000, 0.05, rng)
            sv.append(accuracy(w, b, s.x_old_t, s.y_old_t))
            if n == ns[-1]:
                q8v.append(accuracy(quantise_net(w, 8, 'per-channel'), b,
                                    s.x_old_t, s.y_old_t))
                q4v.append(accuracy(quantise_net(w, 4, 'per-channel'), b,
                                    s.x_old_t, s.y_old_t))
        hard.append(float(np.mean(hv)))
        soft.append(float(np.mean(sv)))
    print('--- distillation ---')
    print(f'teacher {t.sizes}: {t.n_param:,} parameters, {t.macs:,} multiply-adds, '
          f'accuracy {t.acc:.3f}')
    print(f'student {student_sizes}: {n_student:,} parameters, '
          f'{macs(student_sizes):,} multiply-adds '
          f'({t.n_param / n_student:.1f} times fewer parameters, '
          f'{t.macs / macs(student_sizes):.1f} times less arithmetic)')
    print(f'  one example, true class {s.y_old[pick]}, teacher raw outputs '
          + ' '.join(f'{v:+.2f}' for v in z))
    for temp, p in rows.items():
        print(f'    temperature {temp:.0f}: ' + ' '.join(f'{v:.3f}' for v in p)
              + f'   information {ent[temp]:.3f} bits')
    print('  student accuracy against the number of teaching examples:')
    print('    examples   ' + ' '.join(f'{n:>6}' for n in ns))
    print('    hard label ' + ' '.join(f'{v:6.3f}' for v in hard))
    print('    soft target' + ' '.join(f'{v:6.3f}' for v in soft))
    print(f'  the same students squeezed: 8 bits {np.mean(q8v):.3f}, '
          f'4 bits {np.mean(q4v):.3f}')
    out = {'ns': ns, 'hard': hard, 'soft': soft, 'rows': rows, 'ent': ent,
           'z': z, 'true': int(s.y_old[pick]), 'n_student': n_student,
           'student_sizes': student_sizes, 'teacher_acc': t.acc,
           'teacher_param': t.n_param, 'teacher_macs': t.macs,
           'q8': float(np.mean(q8v)), 'q4': float(np.mean(q4v))}
    _CACHE['distil'] = out
    return out


def _mask_global(ws: list[Arr], keep: float) -> list[Arr]:
    flat = np.concatenate([np.abs(w).ravel() for w in ws])
    thresh = np.quantile(flat, 1.0 - keep)
    return [w * (np.abs(w) >= thresh) for w in ws]


def _mask_two_of_four(ws: list[Arr]) -> list[Arr]:
    out: list[Arr] = []
    for w in ws:
        rows, cols = w.shape
        g = w.reshape(rows // 4, 4, cols)
        order = np.argsort(-np.abs(g), axis=1)
        m = np.zeros_like(g)
        np.put_along_axis(m, order[:, :2, :], 1.0, axis=1)
        out.append((g * m).reshape(rows, cols))
    return out


def exp_prune() -> dict[str, object]:
    """Magnitude pruning, 2:4 sparsity, and cutting whole neurons out."""
    if 'prune' in _CACHE:
        return _CACHE['prune']           # type: ignore[return-value]
    s = sim()
    b = big()
    sparsities = [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
    uns: list[float] = []
    for sp in sparsities:
        wq = _mask_global(b.w, 1.0 - sp)
        uns.append(accuracy(wq, b.b, s.x_old_t, s.y_old_t))
    two_four = accuracy(_mask_two_of_four(b.w), b.b, s.x_old_t, s.y_old_t)
    # structured: keep the k hidden neurons of each hidden layer with the
    # largest outgoing weights, which really does shrink the matrices
    keeps = [48, 40, 32, 24, 16, 12, 8, 6, 4]
    stru: list[float] = []
    stru_macs: list[int] = []
    stru_sparsity: list[float] = []
    for k in keeps:
        i1 = np.argsort(-np.linalg.norm(b.w[1], axis=1))[:k]
        i1.sort()
        i2 = np.argsort(-np.linalg.norm(b.w[2], axis=1))[:k]
        i2.sort()
        ws = [b.w[0][:, i1], b.w[1][np.ix_(i1, i2)], b.w[2][i2, :]]
        bs = [b.b[0][i1], b.b[1][i2], b.b[2]]
        stru.append(accuracy(ws, bs, s.x_old_t, s.y_old_t))
        sizes = [FEAT, k, k, N_CLASS]
        stru_macs.append(macs(sizes))
        stru_sparsity.append(1.0 - macs(sizes) / b.macs)
    print('--- pruning ---')
    print(f'the full network scores {b.acc:.3f} with {b.macs:,} multiply-adds')
    for sp, a in zip(sparsities, uns):
        print(f'  {100 * sp:4.0f}% of the weights set to zero, scattered: {a:.3f} '
              f'(still {b.macs:,} multiply-adds on ordinary hardware)')
    print(f'  2:4 sparsity, which is 50% zeros in a pattern some hardware can use: '
          f'{two_four:.3f}')
    for k, a, mc, spr in zip(keeps, stru, stru_macs, stru_sparsity):
        print(f'  {k:>2} hidden neurons kept of 48: {a:.3f}, {mc:,} multiply-adds '
              f'({100 * spr:4.1f}% less arithmetic)')
    out = {'sparsities': sparsities, 'uns': uns, 'two_four': two_four,
           'keeps': keeps, 'stru': stru, 'stru_macs': stru_macs,
           'stru_sparsity': stru_sparsity, 'base_macs': b.macs, 'base_acc': b.acc}
    _CACHE['prune'] = out
    return out


def exp_stack() -> dict[str, object]:
    """Distil into a student, then quantise the student: the two methods together.

    The students are the same five runs the distillation curve ends on, so the
    numbers here and in exp_distil are the same kind of number.
    """
    if 'stack' in _CACHE:
        return _CACHE['stack']           # type: ignore[return-value]
    s = sim()
    t = big()
    d = exp_distil()
    sizes: list[int] = d['student_sizes']        # type: ignore[assignment]
    n_student: int = d['n_student']              # type: ignore[assignment]
    rows: list[tuple[str, float, float, float]] = [
        ('teacher, 16 bits a weight', accuracy(t.w, t.b, s.x_old_t, s.y_old_t),
         t.n_param * 2.0, float(t.macs)),
        ('teacher, 4 bits a weight',
         accuracy(quantise_net(t.w, 4, 'per-channel'), t.b, s.x_old_t, s.y_old_t),
         t.n_param * 0.5, float(t.macs)),
        ('student, 16 bits a weight', d['soft'][-1], n_student * 2.0,   # type: ignore[index]
         float(macs(sizes))),
        ('student, 8 bits a weight', d['q8'], n_student * 1.0,          # type: ignore[index]
         float(macs(sizes))),
        ('student, 4 bits a weight', d['q4'], n_student * 0.5,          # type: ignore[index]
         float(macs(sizes))),
    ]
    print('--- the two methods one after the other (mean of 5 students) ---')
    for name, acc, by, mc in rows:
        print(f'  {name:28s} accuracy {acc:.3f}, {by:9,.0f} bytes of weights, '
              f'{mc:7,.0f} multiply-adds')
    print(f'  the 4-bit student is {rows[0][2] / rows[4][2]:.0f} times smaller and '
          f'{rows[0][3] / rows[4][3]:.0f} times less arithmetic than the float teacher, '
          f'for {rows[0][1] - rows[4][1]:.3f} of accuracy')
    out = {'rows': rows}
    _CACHE['stack'] = out
    return out


# ==========================================================================
# PART 4.  The pictures for 03_fine-tuning-and-adapters.md
# ==========================================================================

RUNG_COLOUR: list[str] = [MUTED, SLIDE, LINK, WRIST, GRIP]


def fig_rungs_what_moves() -> None:
    """Section 1: which parts of the model each rung is allowed to change."""
    fig, axes = plt.subplots(1, 5, figsize=(13.8, 6.6), facecolor='white')
    labels = ['a better prompt', 'a head on\nfrozen features',
              f'a rank-{LORA_R} adapter on\nquery and value',
              'unfreeze the\nlast 4 blocks', 'full fine-tune']
    for k, (ax, label) in enumerate(zip(axes, labels)):
        _blank(ax)
        ax.set_xlim(-0.95, 2.6)
        ax.set_ylim(-6.5, 36.6)
        moved_emb = (k == 4)
        ax.add_patch(Rectangle((0, -1.5), 1.3, 1.1,
                               facecolor=GRIP if moved_emb else '#e8e8e8',
                               edgecolor=INK, lw=0.8))
        ax.text(0.65, -0.95, 'embeddings', ha='center', va='center', fontsize=7.5,
                color='white' if moved_emb else INK)
        for blk in range(N_BLOCK):
            if k == 4:
                col = GRIP
            elif k == 3 and blk >= N_BLOCK - UNFROZEN_BLOCKS:
                col = WRIST
            else:
                col = '#e8e8e8'
            ax.add_patch(Rectangle((0, blk), 1.3, 0.82, facecolor=col,
                                   edgecolor='#999999', lw=0.45))
            if k == 2:
                ax.add_patch(Rectangle((1.38, blk + 0.1), 0.26, 0.62, facecolor=LINK,
                                       edgecolor='none'))
        ax.add_patch(Rectangle((0, 32.6), 1.3, 1.1,
                               facecolor=GRIP if k == 4 else '#e8e8e8',
                               edgecolor=INK, lw=0.8))
        ax.text(0.65, 33.15, 'output head', ha='center', va='center', fontsize=7.5,
                color='white' if k == 4 else INK)
        if k == 1:
            ax.add_patch(Rectangle((0, 34.3), 1.3, 1.1, facecolor=SLIDE,
                                   edgecolor=INK, lw=0.8))
            ax.text(0.65, 34.85, 'new head', ha='center', va='center', fontsize=7.5,
                    color='white')
        if k == 0:
            ax.annotate('', xy=(-0.45, 18.0), xytext=(-0.45, -1.2),
                        arrowprops=dict(arrowstyle='-|>', color=PURPLE, lw=2.0))
            ax.text(-0.62, 8.0, 'a longer input', rotation=90, ha='center', va='center',
                    fontsize=8.5, color=PURPLE)
            ax.text(1.75, 16.0, '32 transformer\nblocks', rotation=90, ha='center',
                    va='center', fontsize=8.5, color=MUTED)
        if k == 2:
            ax.text(2.15, 16.0, 'a thin side path\non two matrices\nin every block',
                    rotation=90, ha='center', va='center', fontsize=8.0, color=LINK)
        pct = 100.0 * RUNG_TRAIN[k] / TOTAL
        ax.set_title(label, fontsize=10.5, color=RUNG_COLOUR[k], weight='bold', pad=8)
        ax.text(0.65, -3.3, f'{RUNG_TRAIN[k]:,}', ha='center', va='center',
                fontsize=10.0, color=RUNG_COLOUR[k], weight='bold')
        ax.text(0.65, -4.6, 'numbers trained', ha='center', va='center', fontsize=8.5,
                color=INK)
        ax.text(0.65, -5.8, f'{pct:.4f}% of the model', ha='center', va='center',
                fontsize=8.5, color=MUTED)
    fig.suptitle('The five rungs: grey parts never change, coloured parts are what '
                 'training is allowed to move',
                 fontsize=12.5, weight='bold', y=1.03)
    _save(fig, FT_DOC, 'rungs-what-moves.svg')


def fig_rung_trainable_bars() -> None:
    """Section 1: the trainable count of each rung, on a log scale."""
    fig, ax = plt.subplots(figsize=(10.6, 4.9), facecolor='white')
    _plain(ax)
    names = [r.replace('\n', ' ') for r in RUNGS]
    vals = [max(v, 1) for v in RUNG_TRAIN]
    y = np.arange(len(names))
    ax.barh(y, vals, color=RUNG_COLOUR, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10)
    ax.invert_yaxis()
    ax.set_xscale('log')
    ax.set_xlim(0.5, 4e11)
    ax.set_xlabel('numbers that training is allowed to change (log scale)', fontsize=10)
    for i, (v, t) in enumerate(zip(vals, RUNG_TRAIN)):
        txt = 'none at all' if t == 0 else f'{t:,}  ({100.0 * t / TOTAL:.4f}% of the model)'
        ax.text(v * 1.4, i, txt, va='center', fontsize=9.5, color=INK)
    ax.set_title(f'One rung to the next multiplies the work: 0, then {NEW_HEAD:,}, then '
                 f'{LORA_QV:,}, then {LAST_BLOCKS:,}, then all {TOTAL:,}',
                 fontsize=11.5, weight='bold')
    ax.grid(axis='x', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'rung-trainable-bars.svg')


def fig_prompt_cost_crossover() -> None:
    """Section 1: when a longer prompt has cost more arithmetic than a fine-tune."""
    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    calls = np.logspace(1.5, 5.6, 250)
    prompt = calls * PROMPT_FLOP_PER_CALL / 1e15
    ax.plot(calls, prompt, color=PURPLE, lw=2.4,
            label=f'{PROMPT_TOKENS} extra prompt tokens on every call')
    ax.axhline(FT_FLOP / 1e15, color=GRIP, lw=2.4, ls='--',
               label=f'one fine-tune on {FT_TOKENS:,} tokens, paid once')
    ax.axvline(CROSSOVER_CALLS, color=INK, lw=1.0, ls=':')
    ax.plot([CROSSOVER_CALLS], [FT_FLOP / 1e15], 'o', color=INK, ms=7)
    ax.annotate(f'they cost the same after\n{CROSSOVER_CALLS:,.0f} calls',
                xy=(CROSSOVER_CALLS, FT_FLOP / 1e15),
                xytext=(CROSSOVER_CALLS * 3.0, FT_FLOP / 1e15 * 0.16),
                fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.2))
    ax.annotate(f'at 100,000 calls the prompt has cost\n'
                f'{100000 * PROMPT_FLOP_PER_CALL / 1e15:,.0f} PFLOP, '
                f'{100000 * PROMPT_FLOP_PER_CALL / FT_FLOP:.0f} times the fine-tune',
                xy=(1e5, 1e5 * PROMPT_FLOP_PER_CALL / 1e15),
                xytext=(2.2e3, 1.4e3), fontsize=9.5, color=PURPLE,
                arrowprops=dict(arrowstyle='-|>', color=PURPLE, lw=1.2))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('number of times the model is called', fontsize=10)
    ax.set_ylabel('arithmetic used, PFLOP (log scale)', fontsize=10)
    ax.set_title(f'A longer prompt is free once and expensive forever: the crossover for '
                 f'this {_big(TOTAL)}-parameter model is {CROSSOVER_CALLS:,.0f} calls',
                 fontsize=11.5, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'prompt-cost-crossover.svg')


def fig_bytes_you_ship() -> None:
    """Section 1: how many bytes each rung leaves you to store for every new job."""
    fig, ax = plt.subplots(figsize=(10.6, 4.9), facecolor='white')
    _plain(ax)
    names = [r.replace('\n', ' ') for r in RUNGS]
    changed = [0, NEW_HEAD * 2, LORA_QV * 2, LAST_BLOCKS * 2, TOTAL * 2]
    y = np.arange(len(names))
    ax.barh(y, [max(v, 1) for v in changed], color=RUNG_COLOUR, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10)
    ax.invert_yaxis()
    ax.set_xscale('log')
    ax.set_xlim(0.5, 1e12)
    ax.set_xlabel('bytes you have to store for each extra job, at 2 bytes a number '
                  '(log scale)', fontsize=10)
    for i, v in enumerate(changed):
        if v == 0:
            txt = 'nothing: the prompt is text'
        elif v < 2 ** 20:
            txt = f'{v / 2 ** 10:,.0f} KiB'
        elif v < 2 ** 30:
            txt = f'{v / 2 ** 20:,.0f} MiB'
        else:
            txt = f'{v / 2 ** 30:,.2f} GiB'
        ax.text(max(v, 1) * 1.5, i, txt, va='center', fontsize=9.5, color=INK)
    ax.set_title('Twenty jobs, twenty adapters of 8 MiB each, or twenty copies of a '
                 '12.55 GiB model',
                 fontsize=11.5, weight='bold')
    ax.grid(axis='x', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'bytes-you-ship.svg')


def fig_model_shape() -> None:
    """Section 2: where the 6.74 billion parameters sit."""
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11.4, 5.6), facecolor='white',
                                  gridspec_kw={'height_ratios': [1.0, 1.25]})
    _blank(ax)
    parts = [('embedding table\n32000 x 4096', EMB, TEAL),
             ('attention in 32 blocks\n4 x 4096 x 4096 each', N_BLOCK * ATT_PER_BLOCK, LINK),
             ('feed-forward in 32 blocks\n3 x 4096 x 11008 each', N_BLOCK * FF_PER_BLOCK, WRIST),
             ('output head\n32000 x 4096', OUT_HEAD, PURPLE)]
    left = 0.0
    for name, val, col in parts:
        ax.add_patch(Rectangle((left, 0.25), val, 0.5, facecolor=col, edgecolor='white',
                               lw=1.2))
        mid = left + val / 2
        if val / TOTAL > 0.08:
            ax.text(mid, 0.5, f'{100.0 * val / TOTAL:.1f}%', ha='center', va='center',
                    fontsize=10, color='white', weight='bold')
        else:
            ax.text(mid, 0.14, f'{100.0 * val / TOTAL:.1f}%', ha='center', va='top',
                    fontsize=9.5, color=col, weight='bold')
        left += val
    ax.set_xlim(0, TOTAL)
    ax.set_ylim(0, 1.0)
    ax.text(0, 0.86, f'all {TOTAL:,} parameters', fontsize=10, color=INK)
    _plain(ax2)
    names = [p[0] for p in parts] + ['all the normalisation\nscales together']
    vals = [p[1] for p in parts] + [N_BLOCK * NORM_PER_BLOCK + FINAL_NORM]
    cols = [p[2] for p in parts] + [MUTED]
    xx = np.arange(len(names))
    ax2.bar(xx, vals, color=cols, width=0.6)
    ax2.set_yscale('log')
    ax2.set_xticks(xx)
    ax2.set_xticklabels(names, fontsize=8.8)
    ax2.set_ylabel('parameters (log scale)', fontsize=10)
    ax2.set_ylim(1e4, 1e10)
    for x, v in zip(xx, vals):
        ax2.text(x, v * 1.5, f'{v:,}', ha='center', fontsize=9, color=INK)
    fig.suptitle('The stated model: 32 blocks of width 4096 come to '
                 f'{TOTAL:,} parameters, and the feed-forward part holds two thirds of them',
                 fontsize=11.8, weight='bold', y=0.99)
    _save(fig, FT_DOC, 'model-shape-parameter-count.svg')


def fig_bytes_per_parameter() -> None:
    """Section 2: why one trainable parameter costs six times a frozen one."""
    fig, ax = plt.subplots(figsize=(10.2, 4.4), facecolor='white')
    _blank(ax)
    rows = [('a frozen parameter', [('the weight\nbfloat16', 2, LINK)]),
            ('a parameter being trained',
             [('the weight\nbfloat16', 2, LINK), ('its gradient\nbfloat16', 2, WRIST),
              ('AdamW running\naverage, float32', 4, SLIDE),
              ('AdamW running\nsquare, float32', 4, PURPLE)])]
    for r, (label, pieces) in enumerate(rows):
        yy = 1.0 - r * 0.72
        left = 0.0
        for name, by, col in pieces:
            ax.add_patch(Rectangle((left, yy), by, 0.4, facecolor=col, edgecolor='white',
                                   lw=1.4))
            ax.text(left + by / 2, yy + 0.2, f'{by}', ha='center', va='center',
                    fontsize=11, color='white', weight='bold')
            ax.text(left + by / 2, yy - 0.06, name, ha='center', va='top',
                    fontsize=8.0, color=col)
            left += by
        total = sum(p[1] for p in pieces)
        ax.text(-0.25, yy + 0.2, label, ha='right', va='center', fontsize=10.5, color=INK)
        ax.text(total + 0.2, yy + 0.2, f'{total} bytes', ha='left', va='center',
                fontsize=10.5, color=INK, weight='bold')
    ax.set_xlim(-4.6, 15.0)
    ax.set_ylim(-0.45, 1.75)
    ax.set_title(f'A parameter you train costs {B_TRAIN} bytes while a frozen one costs '
                 f'{B_FROZEN}, which is why freezing saves so much',
                 fontsize=11.8, weight='bold')
    _save(fig, FT_DOC, 'bytes-per-parameter.svg')


def fig_memory_per_rung() -> None:
    """Section 2: the memory each rung needs for weights, gradients and optimiser."""
    fig, ax = plt.subplots(figsize=(11.0, 5.4), facecolor='white')
    _plain(ax)
    names = list(RUNGS)
    xx = np.arange(len(names))
    frozen = []
    grads = []
    optim = []
    for tr, ex in zip(RUNG_TRAIN, RUNG_EXTRA):
        frozen.append(_gib((TOTAL + ex) * 2))
        grads.append(_gib(tr * 2))
        optim.append(_gib(tr * 8))
    ax.bar(xx, frozen, color=LINK, width=0.58, label='every weight, bfloat16')
    ax.bar(xx, grads, bottom=frozen, color=WRIST, width=0.58,
           label='gradients of the trained weights')
    ax.bar(xx, optim, bottom=np.array(frozen) + np.array(grads), color=PURPLE, width=0.58,
           label='AdamW state for the trained weights')
    ax.axhline(CARD_GIB, color=GRIP, lw=2.0, ls='--')
    ax.text(-0.42, CARD_GIB + 1.8, f'a {CARD_GIB:.0f} GiB graphics card', ha='left',
            fontsize=9.5, color=GRIP)
    for x, by in zip(xx, RUNG_BYTES):
        ax.text(x, _gib(by) + 2.0, f'{_gib(by):.2f} GiB', ha='center', fontsize=9.8,
                color=INK, weight='bold',
                bbox=dict(boxstyle='round,pad=0.18', facecolor='white', edgecolor='none'))
    ax.set_xticks(xx)
    ax.set_xticklabels(names, fontsize=9.5)
    ax.set_ylabel('memory for weights, gradients and optimiser state (GiB)', fontsize=10)
    ax.set_ylim(0, 86)
    ax.set_title('Full fine-tuning needs 75.31 GiB before a single activation is stored, '
                 'and a rank-8 adapter needs 12.60 GiB',
                 fontsize=11.8, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper left')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'memory-per-rung.svg')


def fig_unfreeze_blocks() -> None:
    """Section 2: memory and trainable count as more blocks are unfrozen."""
    ks = np.arange(0, N_BLOCK + 1)
    mem = np.array([_gib(TOTAL * B_FROZEN + k * BLOCK * (B_TRAIN - B_FROZEN)) for k in ks])
    trainable = ks * BLOCK
    fits = int((CARD_GIB * 2 ** 30 - TOTAL * B_FROZEN) // (BLOCK * (B_TRAIN - B_FROZEN)))
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.6, 4.9), facecolor='white')
    _plain(ax)
    ax.plot(ks, mem, color=WRIST, lw=2.4)
    ax.axhline(CARD_GIB, color=GRIP, lw=2.0, ls='--')
    ax.text(31.5, CARD_GIB + 2.0, f'{CARD_GIB:.0f} GiB card', ha='right', fontsize=9.5,
            color=GRIP)
    ax.axvline(fits, color=INK, lw=1.0, ls=':')
    ax.plot([fits], [mem[fits]], 'o', color=INK, ms=7)
    ax.annotate(f'{fits} blocks fit\n({mem[fits]:.2f} GiB)', xy=(fits, mem[fits]),
                xytext=(fits + 4.0, 44.0), fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.2))
    ax.set_xlabel('number of blocks unfrozen, counting back from the last', fontsize=10)
    ax.set_ylabel('memory needed (GiB)', fontsize=10)
    ax.set_xlim(0, 32)
    ax.set_ylim(0, 82)
    ax.set_title('Memory climbs 1.88 GiB for every block you unfreeze',
                 fontsize=11.0, weight='bold')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _plain(ax2)
    ax2.plot(ks, 100.0 * trainable / TOTAL, color=LINK, lw=2.4)
    ax2.plot([UNFROZEN_BLOCKS], [100.0 * LAST_BLOCKS / TOTAL], 'o', color=GRIP, ms=7)
    ax2.annotate(f'4 blocks is {LAST_BLOCKS:,} numbers\n'
                 f'({100.0 * LAST_BLOCKS / TOTAL:.1f}% of the model)',
                 xy=(UNFROZEN_BLOCKS, 100.0 * LAST_BLOCKS / TOTAL),
                 xytext=(13.0, 15.0), fontsize=9.5, color=GRIP,
                 arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.2))
    ax2.set_xlabel('number of blocks unfrozen', fontsize=10)
    ax2.set_ylabel('share of the model being trained (%)', fontsize=10)
    ax2.set_xlim(0, 32)
    ax2.set_ylim(0, 100)
    ax2.set_title('Each block is 3.00% of the model', fontsize=11.0, weight='bold')
    ax2.grid(color=GRID, lw=0.6, alpha=0.6)
    ax2.set_axisbelow(True)
    _save(fig, FT_DOC, 'unfreeze-how-many-blocks.svg')


def fig_lora_two_thin_matrices() -> None:
    """Section 3: the one big matrix and the two thin ones drawn to scale."""
    fig, ax = plt.subplots(figsize=(11.6, 5.8), facecolor='white')
    _blank(ax)
    side = 4.0
    thin = side * LORA_R / D_MODEL * 60      # drawn 60 times wider than true, to be visible
    ax.add_patch(Rectangle((0, 0), side, side, facecolor=LINK_PALE, edgecolor=LINK, lw=1.6))
    ax.text(side / 2, side / 2, f'W\n{D_MODEL} rows\n{D_MODEL} columns\n\n'
                                f'{FULL_MATRIX:,} numbers\nfrozen',
            ha='center', va='center', fontsize=10.5, color=INK)
    ax.text(side / 2, side + 0.22, 'the weight matrix already in the model',
            ha='center', fontsize=10, color=LINK, weight='bold')
    ax.text(5.1, side / 2, '+', ha='center', va='center', fontsize=22, color=INK)
    ax.add_patch(Rectangle((5.9, 0), thin, side, facecolor='#f5d9c4', edgecolor=WRIST, lw=1.6))
    ax.text(5.9 + thin / 2, -0.3, f'A\n{D_MODEL} x {LORA_R}\n{D_MODEL * LORA_R:,} numbers',
            ha='center', va='top', fontsize=9.5, color=WRIST)
    ax.text(5.9 + thin + 0.32, side / 2, 'x', ha='center', va='center', fontsize=18,
            color=INK)
    ax.add_patch(Rectangle((6.5 + thin, side / 2 - thin / 2), side, thin,
                           facecolor='#d7cdee', edgecolor=PURPLE, lw=1.6))
    ax.text(6.5 + thin + side / 2, side / 2 + thin / 2 + 0.22,
            f'B    {LORA_R} x {D_MODEL}    {LORA_R * D_MODEL:,} numbers',
            ha='center', va='bottom', fontsize=9.5, color=PURPLE)
    ax.annotate('', xy=(11.6, side / 2), xytext=(10.9, side / 2),
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.6))
    ax.add_patch(Rectangle((12.0, 0), side, side, facecolor='#ffe9e9', edgecolor=GRIP,
                           lw=1.6))
    ax.text(12.0 + side / 2, side / 2,
            f'A x B\n{D_MODEL} rows\n{D_MODEL} columns\n\nthe same shape as W,\n'
            f'built from only\n{2 * LORA_R * D_MODEL:,} numbers',
            ha='center', va='center', fontsize=10.5, color=INK)
    ax.set_xlim(-0.4, 16.6)
    ax.set_ylim(-1.5, 5.0)
    ax.set_title(f'A rank-{LORA_R} adapter: {2 * LORA_R * D_MODEL:,} trained numbers stand '
                 f'in for a change to all {FULL_MATRIX:,}, which is '
                 f'{100.0 * 2 * LORA_R * D_MODEL / FULL_MATRIX:.3f}% of them',
                 fontsize=11.8, weight='bold')
    ax.text(8.2, -1.25, 'The two thin blocks are drawn 60 times wider than they really are, '
                        'or they would be thinner than this line.',
            ha='center', fontsize=8.5, color=MUTED)
    _save(fig, FT_DOC, 'lora-two-thin-matrices.svg')


def fig_lora_rank_counts() -> None:
    """Section 3: trained numbers against the rank, for one 4096 x 4096 matrix."""
    counts = [lora_count(D_MODEL, D_MODEL, r) for r in RANKS]
    fig, ax = plt.subplots(figsize=(10.8, 5.4), facecolor='white')
    _plain(ax)
    xx = np.arange(len(RANKS))
    ax.bar(xx, counts, color=LINK, width=0.6)
    ax.axhline(FULL_MATRIX, color=GRIP, lw=2.0, ls='--')
    ax.text(-0.42, FULL_MATRIX * 1.25, f'the whole matrix: {FULL_MATRIX:,} numbers',
            fontsize=9.5, color=GRIP)
    for x, (r, c) in enumerate(zip(RANKS, counts)):
        ax.text(x, c * 1.25, f'{c:,}', ha='center', fontsize=9, color=INK)
        ax.text(x, c * 0.55, f'{100.0 * c / FULL_MATRIX:.2f}%', ha='center', fontsize=8.5,
                color='white', weight='bold')
    ax.set_xticks(xx)
    ax.set_xticklabels([f'rank {r}' for r in RANKS], fontsize=9.5)
    ax.set_yscale('log')
    ax.set_ylim(3e3, 1.1e8)
    ax.set_ylabel('numbers you train (log scale)', fontsize=10)
    ax.set_title(f'Doubling the rank doubles the work, and the two shapes only break even '
                 f'at rank {FULL_MATRIX // (2 * D_MODEL):,}',
                 fontsize=11.8, weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'lora-rank-counts.svg')


def fig_lora_where() -> None:
    """Section 3: the seven weight matrices of a block, and three places to attach."""
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14.6, 5.6), facecolor='white',
                                  gridspec_kw={'width_ratios': [1.15, 1.0], 'wspace': 0.52})
    _blank(ax)
    mats = [('query', D_MODEL, D_MODEL, LINK), ('key', D_MODEL, D_MODEL, LINK),
            ('value', D_MODEL, D_MODEL, LINK), ('output', D_MODEL, D_MODEL, LINK),
            ('gate', D_MODEL, D_FF, WRIST), ('up', D_MODEL, D_FF, WRIST),
            ('down', D_FF, D_MODEL, WRIST)]
    for i, (name, rows, cols, col) in enumerate(mats):
        y = 6 - i
        ax.add_patch(Rectangle((0, y), 4.3, 0.76, facecolor=col, alpha=0.20,
                               edgecolor=col, lw=1.1))
        ax.text(0.14, y + 0.38, name, va='center', fontsize=10, color=INK)
        ax.text(1.25, y + 0.38, f'{rows} x {cols}', va='center', fontsize=9.3, color=MUTED)
        ax.text(4.16, y + 0.38, f'{rows * cols:,}', va='center', ha='right', fontsize=9.3,
                color=INK)
        n8 = lora_count(rows, cols, LORA_R)
        ax.text(6.4, y + 0.38, f'{n8:,}', va='center', ha='right', fontsize=9.3, color=col)
    ax.text(1.25, 7.15, 'its shape', fontsize=9.3, color=MUTED, weight='bold')
    ax.text(4.16, 7.15, 'numbers in it', ha='right', fontsize=9.3, color=MUTED,
            weight='bold')
    ax.text(6.4, 7.0, f'a rank-{LORA_R} adapter\nwould train', ha='right', fontsize=9.3,
            color=MUTED, weight='bold')
    ax.text(-0.12, 6.4, 'attention', rotation=90, ha='right', va='center', fontsize=9.3,
            color=LINK)
    ax.text(-0.12, 1.15, 'feed-forward', rotation=90, ha='right', va='center',
            fontsize=9.3, color=WRIST)
    ax.set_xlim(-0.95, 6.6)
    ax.set_ylim(-0.3, 8.0)
    ax.set_title('The seven weight matrices in one block', fontsize=11.5, weight='bold')
    _plain(ax2)
    names = list(ATTACH.keys())
    vals = [ATTACH[n] for n in names]
    yy = np.arange(len(names))
    ax2.barh(yy, vals, color=[LINK, TEAL, WRIST], height=0.5)
    ax2.set_yticks(yy)
    ax2.set_yticklabels([n.replace(' and ', ' and\n') for n in names], fontsize=9.5)
    ax2.invert_yaxis()
    ax2.set_xlim(0, 3.4e7)
    for y, v in zip(yy, vals):
        ax2.text(v * 1.04, y, f'{v:,} numbers\n{100.0 * v / TOTAL:.4f}% of the model',
                 va='center', fontsize=9.3, color=INK)
    ax2.set_xlabel('numbers you train, over all 32 blocks', fontsize=10)
    ax2.set_title(f'Where you attach the rank-{LORA_R} adapters', fontsize=11.5,
                  weight='bold')
    ax2.grid(axis='x', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    _save(fig, FT_DOC, 'lora-where-in-the-block.svg')


def fig_lora_scaling_folding() -> None:
    """Section 3: what the scaling factor does, and that folding changes nothing."""
    d = lora_scaling()
    ranks = d['ranks']                       # type: ignore[index]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(ranks, d['raw'], marker='o', color=GRIP, lw=2.2,         # type: ignore[arg-type]
            label='no scaling at all')
    ax.plot(ranks, d['by_r'], marker='s', color=LINK, lw=2.2,        # type: ignore[arg-type]
            label='multiplied by alpha / rank')
    ax.plot(ranks, d['by_sqrt'], marker='^', color=SLIDE, lw=2.2,    # type: ignore[arg-type]
            label='multiplied by alpha / square root of rank')
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(ranks)
    ax.set_xticklabels([str(r) for r in ranks])
    ax.set_xlabel('rank of the adapter', fontsize=10)
    ax.set_ylabel('size of the change the adapter adds (log scale)', fontsize=10)
    ax.set_title('With no scaling the adapter pushes harder as the rank grows',
                 fontsize=11.2, weight='bold')
    ax.legend(fontsize=9.3, frameon=False, loc='lower left')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _blank(ax2)
    mac_w: int = d['mac_w']                  # type: ignore[assignment]
    mac_side: int = d['mac_side']            # type: ignore[assignment]
    bars = [('the matrix on its own', mac_w, LINK),
            ('with a separate side path', mac_w + mac_side, WRIST),
            ('with the adapter folded in', mac_w, SLIDE)]
    for i, (name, v, col) in enumerate(bars):
        y = 2 - i
        ax2.add_patch(Rectangle((0, y), v / mac_w * 6.0, 0.55, facecolor=col,
                                edgecolor='none'))
        ax2.text(0.12, y + 0.275, name, va='center', fontsize=10, color='white')
        ax2.text(v / mac_w * 6.0 + 0.12, y + 0.275, f'{v:,} multiply-adds', va='center',
                 fontsize=9.6, color=INK)
    ax2.text(0.0, -0.5,
             'The folded weights give the same answer as the separate side path:\n'
             f'the largest difference between the two is {d["gap"]:.1e}, which is only '
             'the rounding\nof the arithmetic itself. So a folded adapter costs nothing '
             'at all when the model runs.',
             fontsize=9.6, color=INK, va='top')
    ax2.set_xlim(-0.1, 9.6)
    ax2.set_ylim(-1.7, 3.1)
    ax2.set_title('Folding the adapter back into the weights', fontsize=11.2, weight='bold')
    _save(fig, FT_DOC, 'lora-scaling-and-folding.svg')


def fig_qlora_memory() -> None:
    """Section 4: what fits on one card once the base is squeezed to 4 bits."""
    bpw = bits_per_weight(4, 64)
    base4 = TOTAL * bpw / 8
    base16 = TOTAL * 2.0
    adapter = LORA_QV * B_TRAIN
    fig, ax = plt.subplots(figsize=(10.6, 5.4), facecolor='white')
    _plain(ax)
    names = ['full fine-tune,\nbfloat16 weights', 'rank-8 adapter,\nbfloat16 base',
             'rank-8 adapter,\n4-bit base']
    base = [_gib(TOTAL * 2), _gib(base16), _gib(base4)]
    rest = [_gib(TOTAL * 10), _gib(adapter), _gib(adapter)]
    xx = np.arange(3)
    ax.bar(xx, base, color=LINK, width=0.52, label='the frozen weights')
    ax.bar(xx, rest, bottom=base, color=PURPLE, width=0.52,
           label='gradients and optimiser state for what is trained')
    ax.axhline(CARD_GIB, color=GRIP, lw=2.0, ls='--')
    ax.text(2.45, CARD_GIB + 1.8, f'a {CARD_GIB:.0f} GiB graphics card', fontsize=9.5,
            color=GRIP, ha='right')
    for x, (b, r) in enumerate(zip(base, rest)):
        ax.text(x, b + r + 1.8, f'{b + r:.2f} GiB', ha='center', fontsize=10, color=INK,
                weight='bold',
                bbox=dict(boxstyle='round,pad=0.18', facecolor='white', edgecolor='none'))
    ax.set_xticks(xx)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylabel('memory before any activations (GiB)', fontsize=10)
    ax.set_ylim(0, 86)
    ax.set_title(f'A 4-bit base plus a rank-8 adapter needs {_gib(base4 + adapter):.2f} GiB, '
                 f'so most of a {CARD_GIB:.0f} GiB card is left for the rest of the work',
                 fontsize=11.6, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'qlora-memory-stack.svg')


def fig_qlora_groups() -> None:
    """Section 4: the scales cost bits too, and smaller groups cost more."""
    d = exp_per_channel()
    b = big()
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.8, 4.9), facecolor='white')
    _plain(ax)
    groups = [32, 64, 128, 256, 1024]
    bpws = [bits_per_weight(4, g) for g in groups]
    xx = np.arange(len(groups))
    ax.bar(xx, [4.0] * len(groups), color=LINK, width=0.55, label='the 4-bit integers')
    ax.bar(xx, [v - 4.0 for v in bpws], bottom=4.0, color=WRIST, width=0.55,
           label='a 16-bit scale for each group')
    for x, (g, v) in enumerate(zip(groups, bpws)):
        ax.text(x, v + 0.04, f'{v:.3f} bits\n{_gib(TOTAL * v / 8):.2f} GiB', ha='center',
                fontsize=9.2, color=INK)
    ax.set_xticks(xx)
    ax.set_xticklabels([f'{g} weights\nto a scale' for g in groups], fontsize=9.3)
    ax.set_ylim(0, 6.2)
    ax.set_ylabel('bits stored for each weight', fontsize=10)
    ax.set_title('What the scales add to four bits', fontsize=11.2, weight='bold')
    ax.legend(fontsize=9.3, frameon=False, loc='upper right')
    _plain(ax2)
    w = b.w[1]
    gsizes = [8, 16, 24, 48]
    errs = []
    for g in gsizes:
        deq, _q, _s = quantise(w, 4, 'grouped', g)
        errs.append(100.0 * rms(deq - w) / rms(w))
    deq, _q, _s = quantise(w, 4, 'per-tensor')
    per_tensor = 100.0 * rms(deq - w) / rms(w)
    xs = [16.0 / g for g in gsizes]
    ax2.plot(xs, errs, marker='o', color=LINK, lw=2.2)
    for x, g, e in zip(xs, gsizes, errs):
        ax2.annotate(f'groups of {g}\n{e:.2f}%', xy=(x, e), xytext=(x, e + 0.22),
                     fontsize=9.0, color=INK, ha='center')
    ax2.axhline(per_tensor, color=GRIP, lw=1.8, ls='--')
    ax2.text(0.28, per_tensor - 0.75, f'one scale for the whole matrix: {per_tensor:.2f}%',
             fontsize=9.3, color=GRIP)
    ax2.set_xlim(0.2, 2.35)
    ax2.set_xlabel('extra bits per weight spent on scales', fontsize=10)
    ax2.set_ylabel('error left after reading the weights back (%)', fontsize=10)
    ax2.set_ylim(min(errs) - 0.5, per_tensor + 1.4)
    ax2.set_title('Measured on a real trained 48 x 48 weight matrix', fontsize=11.2,
                  weight='bold')
    ax2.grid(color=GRID, lw=0.6, alpha=0.6)
    ax2.set_axisbelow(True)
    _save(fig, FT_DOC, 'qlora-bits-and-groups.svg')


def fig_qlora_recovers() -> None:
    """Section 4: an adapter on a 4-bit base gets back nearly all of the loss."""
    d = exp_quant_adapter()
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.0), facecolor='white')
    _plain(ax)
    names = ['float base', '8-bit base', '4-bit base']
    vals = [d['old job, float base'], d['old job, 8-bit base'], d['old job, 4-bit base']]
    xx = np.arange(3)
    ax.bar(xx, vals, color=[LINK, TEAL, WRIST], width=0.55)
    for x, v in zip(xx, vals):
        ax.text(x, v + 0.008, f'{v:.3f}', ha='center', fontsize=10.5, color=INK,
                weight='bold')
    ax.set_xticks(xx)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(0.8, 0.98)
    ax.set_ylabel('accuracy on the old six-way job', fontsize=10)
    ax.set_title('Squeezing the frozen base to 4 bits costs '
                 f'{d["old job, float base"] - d["old job, 4-bit base"]:.3f} of accuracy',
                 fontsize=11.2, weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _plain(ax2)
    labels = ['4-bit base,\nno adapter', 'float base +\nrank-2 adapter',
              '8-bit base +\nrank-2 adapter', '4-bit base +\nrank-2 adapter']
    keys = ['4-bit base, no adapter', 'float base + rank-2 adapter',
            '8-bit base + rank-2 adapter', '4-bit base + rank-2 adapter']
    vals2 = [d[k] for k in keys]
    xx2 = np.arange(len(labels))
    ax2.bar(xx2, vals2, color=[MUTED, LINK, TEAL, WRIST], width=0.58)
    for x, v in zip(xx2, vals2):
        ax2.text(x, v + 0.008, f'{v:.3f}', ha='center', fontsize=10.5, color=INK,
                 weight='bold')
    ax2.set_xticks(xx2)
    ax2.set_xticklabels(labels, fontsize=9.5)
    ax2.set_ylim(0.4, 0.84)
    ax2.set_ylabel('accuracy on the new job after 64 examples', fontsize=10)
    ax2.set_title('A small adapter on a squeezed base still learns the new job',
                  fontsize=11.2, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    _save(fig, FT_DOC, 'qlora-adapter-recovers.svg')


def fig_forgetting_curves() -> None:
    """Section 5: the old job falls apart while the new one is being learned."""
    d = exp_forgetting()
    s = sim()
    hist = d['hist']                         # type: ignore[index]
    old, new = hist[0], hist[1]              # type: ignore[index]
    steps = np.arange(len(old))
    fig, ax = plt.subplots(figsize=(11.0, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(steps, old, color=GRIP, lw=2.4, label='the old six-way job it was pretrained on')
    ax.plot(steps, new, color=LINK, lw=2.4, label='the narrow new two-way job')
    ax.axhline(1.0 / N_CLASS, color=MUTED, lw=1.2, ls=':')
    ax.text(150, 1.0 / N_CLASS - 0.055, 'pure guessing on the old job', ha='center',
            fontsize=9, color=MUTED)
    for st, dx in ((10, 10), (50, 10), (300, -36)):
        ax.plot([st], [old[st]], 'o', color=GRIP, ms=6)
        ax.annotate(f'{old[st]:.3f}', xy=(st, old[st]), xytext=(st + dx, old[st] + 0.045),
                    fontsize=9.3, color=GRIP)
    ax.plot([0], [s.acc_old], 'o', color=GRIP, ms=6)
    ax.annotate(f'{s.acc_old:.3f} before a single step', xy=(0, s.acc_old),
                xytext=(26, s.acc_old + 0.03), fontsize=9.3, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.0))
    ax.set_xlabel('steps of a hard full fine-tune on the new job', fontsize=10)
    ax.set_ylabel('accuracy on a held-out test set', fontsize=10)
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 1.03)
    ax.set_title('Ten steps buy most of the new job and have already cost a quarter of the '
                 'old one', fontsize=11.8, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='center right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'forgetting-curves.svg')


def fig_forgetting_what_helps() -> None:
    """Section 5: six recipes, and what each leaves of the old job."""
    d = exp_forgetting()
    recipes = d['recipes']                   # type: ignore[index]
    names = [r[0] for r in recipes]
    old = [r[1] for r in recipes]
    new = [r[2] for r in recipes]
    fig, ax = plt.subplots(figsize=(12.4, 5.4), facecolor='white')
    _plain(ax)
    xx = np.arange(len(names))
    ax.bar(xx - 0.19, old, width=0.36, color=GRIP, label='the old six-way job')
    ax.bar(xx + 0.19, new, width=0.36, color=LINK, label='the new two-way job')
    for x, (o, n) in enumerate(zip(old, new)):
        ax.text(x - 0.19, o + 0.014, f'{o:.3f}', ha='center', fontsize=9.2, color=INK)
        ax.text(x + 0.19, n + 0.014, f'{n:.3f}', ha='center', fontsize=9.2, color=INK)
    ax.set_xticks(xx)
    ax.set_xticklabels(names, fontsize=9.2)
    ax.set_ylabel('accuracy on a held-out test set', fontsize=10)
    ax.set_ylim(0, 1.09)
    ax.set_title('Mixing a quarter of the old data back in keeps the old job almost whole, '
                 'and an adapter can simply be switched off',
                 fontsize=11.6, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper left', ncol=2)
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'forgetting-what-helps.svg')


def fig_forgetting_mix() -> None:
    """Section 5: how much of the old data has to go back into each batch."""
    rows = exp_mix_fraction()
    fracs = [r[0] for r in rows]
    old = [r[1] for r in rows]
    new = [r[2] for r in rows]
    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    xx = np.arange(len(fracs))
    ax.plot(xx, old, marker='o', color=GRIP, lw=2.4, label='the old six-way job')
    ax.plot(xx, new, marker='s', color=LINK, lw=2.4, label='the new two-way job')
    for x, (o, n) in enumerate(zip(old, new)):
        ax.annotate(f'{o:.3f}', xy=(x, o), xytext=(x, o + 0.035), ha='center',
                    fontsize=9.2, color=GRIP)
        ax.annotate(f'{n:.3f}', xy=(x, n), xytext=(x, n - 0.055), ha='center',
                    fontsize=9.2, color=LINK)
    ax.set_xticks(xx)
    ax.set_xticklabels([f'{100 * f:.0f}%' for f in fracs], fontsize=10)
    ax.set_xlabel('old examples added to each batch of new ones', fontsize=10)
    ax.set_ylabel('accuracy on a held-out test set', fontsize=10)
    ax.set_ylim(0, 1.09)
    ax.set_title(f'Adding only 5% of the old data lifts the old job from {old[0]:.3f} to '
                 f'{old[1]:.3f}, and the new job does not suffer',
                 fontsize=11.6, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'forgetting-mix-fraction.svg')


def fig_forgetting_frontier() -> None:
    """Section 5: every learning rate and length, plotted as a trade-off."""
    d = exp_forgetting()
    front = d['front']                       # type: ignore[index]
    lrs = sorted({f[0] for f in front})
    cols = [TEAL, SLIDE, LINK, WRIST, GRIP]
    fig, ax = plt.subplots(figsize=(10.8, 5.6), facecolor='white')
    _plain(ax)
    for lr, col in zip(lrs, cols):
        pts = sorted([(f[1], f[3], f[2]) for f in front if f[0] == lr])
        ax.plot([p[1] for p in pts], [p[2] for p in pts], marker='o', color=col, lw=1.8,
                ms=6, label=f'learning rate {lr}')
        for st, nx, oy in (pts[0], pts[-1]):
            pass
        ax.annotate(f'{pts[0][0]} steps', xy=(pts[0][1], pts[0][2]),
                    xytext=(pts[0][1] - 0.012, pts[0][2] + 0.022), fontsize=8.4, color=col,
                    ha='right')
        ax.annotate(f'{pts[-1][0]} steps', xy=(pts[-1][1], pts[-1][2]),
                    xytext=(pts[-1][1] + 0.008, pts[-1][2] - 0.035), fontsize=8.4, color=col)
    s = sim()
    ax.plot([s.acc_new_before], [s.acc_old], '*', color=INK, ms=16)
    ax.annotate('before any fine-tuning', xy=(s.acc_new_before, s.acc_old),
                xytext=(s.acc_new_before - 0.02, s.acc_old - 0.10), fontsize=9.5,
                color=INK, arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0))
    ax.set_xlabel('accuracy on the new two-way job', fontsize=10)
    ax.set_ylabel('accuracy left on the old six-way job', fontsize=10)
    ax.set_xlim(0.46, 0.88)
    ax.set_ylim(0.0, 1.03)
    ax.set_title('Every run is a trade between the two jobs, and each line follows one '
                 'learning rate from 25 steps to 400', fontsize=11.3, weight='bold')
    ax.legend(fontsize=9.3, frameon=False, loc='center left',
              bbox_to_anchor=(0.01, 0.42))
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'forgetting-frontier.svg')


def fig_data_curves() -> None:
    """Section 6: new-job accuracy against the number of new-job examples."""
    c = exp_curves()
    s = sim()
    counts = c['_counts']                    # type: ignore[index]
    fig, ax = plt.subplots(figsize=(11.0, 5.6), facecolor='white')
    _plain(ax)
    styles = [('head', SLIDE, 'o', f'a new head only, {counts[0]:,} numbers'),
              ('lora2', LINK, 's', f'a rank-2 adapter, {counts[1]:,} numbers'),
              ('full', GRIP, '^', f'every weight, {counts[2]:,} numbers')]
    for key, col, mk, label in styles:
        ax.plot(CURVE_N, c[key], marker=mk, color=col, lw=2.2, ms=6, label=label)
    ax.axhline(s.acc_new_before, color=MUTED, lw=1.6, ls=':')
    ax.text(4.2, s.acc_new_before - 0.028, f'before any tuning: {s.acc_new_before:.3f}',
            fontsize=9.3, color=MUTED)
    ax.axhline(s.ceiling, color=INK, lw=1.6, ls='--')
    ax.text(4.2, s.ceiling + 0.012, f'nothing can beat {s.ceiling:.3f} on this job',
            fontsize=9.3, color=INK)
    ax.set_xscale('log', base=2)
    ax.set_xticks(CURVE_N)
    ax.set_xticklabels([str(n) for n in CURVE_N])
    ax.set_xlabel('examples of the new job', fontsize=10)
    ax.set_ylabel(f'accuracy on the new job (mean of {REPEATS} runs)', fontsize=10)
    ax.set_ylim(0.44, 0.90)
    ax.set_title('The cheap rungs climb first and then stop, and only full fine-tuning '
                 'reaches the ceiling', fontsize=11.6, weight='bold')
    ax.legend(fontsize=9.6, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, FT_DOC, 'data-learning-curves.svg')


def fig_data_distance() -> None:
    """Section 6: three new jobs at increasing distance from the old one."""
    d = exp_distance()
    ns = d['ns']                             # type: ignore[index]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.4), facecolor='white',
                                  gridspec_kw={'width_ratios': [1.35, 1.0], 'wspace': 0.3})
    _plain(ax)
    cols = [SLIDE, LINK, GRIP]
    for row, ceil, name, col, before in zip(d['curves'], d['ceilings'],   # type: ignore
                                            d['jobs'], cols, d['befores']):   # type: ignore
        ax.plot(ns, row, marker='o', color=col, lw=2.2, ms=5.5,
                label=name.replace('\n', ' '))
        ax.axhline(ceil, color=col, lw=1.0, ls='--', alpha=0.6)
        ax.plot([ns[0] * 0.78], [before], '*', color=col, ms=13)
    ax.text(5.0, 0.865, 'the stars on the left are the accuracy before any fine-tuning',
            fontsize=8.8, color=MUTED, ha='left')
    ax.set_xscale('log', base=2)
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlim(2.6, 620)
    ax.set_xlabel('examples of the new job', fontsize=10)
    ax.set_ylabel('accuracy on the new job', fontsize=10)
    ax.set_ylim(0.45, 1.04)
    ax.set_title('Three new jobs, each further from the old one', fontsize=11.4,
                 weight='bold')
    ax.legend(fontsize=9.2, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _plain(ax2)
    xx = np.arange(3)
    ax2.bar(xx, list(d['befores']), color=cols, width=0.56)   # type: ignore[arg-type]
    for x, (bf, raw) in enumerate(zip(d['befores'], d['needed'])):   # type: ignore[arg-type]
        ax2.text(x, bf + 0.015, f'{bf:.3f}', ha='center', fontsize=10.5, color=INK,
                 weight='bold')
        txt = (f'{raw}\nexamples\nto fix it' if raw is not None
               else 'more than\n512 examples\nneeded')
        ax2.text(x, 0.14, txt, ha='center', va='center', fontsize=8.6, color='white',
                 weight='bold')
    ax2.set_xticks(xx)
    ax2.set_xticklabels(list(d['jobs']), fontsize=8.6)   # type: ignore[arg-type]
    ax2.set_ylim(0, 1.0)
    ax2.set_ylabel('accuracy before any fine-tuning', fontsize=10)
    ax2.set_title('Distance costs accuracy before you start;\na new distinction costs '
                  'examples', fontsize=11.0, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    _save(fig, FT_DOC, 'data-vs-distance.svg')


def fig_data_variation() -> None:
    """Section 6: a more varied job needs more examples."""
    d = exp_variation()
    spreads = d['spreads']                   # type: ignore[index]
    ns = d['ns']                             # type: ignore[index]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white',
                                  gridspec_kw={'width_ratios': [1.3, 1.0], 'wspace': 0.3})
    _plain(ax)
    cols = [TEAL, SLIDE, LINK, WRIST, GRIP]
    for sp, row, ceil, col in zip(spreads, d['curves'], d['ceilings'], cols):  # type: ignore
        ax.plot(ns, row, marker='o', color=col, lw=2.0, ms=5,
                label=f'scatter {sp:.2f}, ceiling {ceil:.3f}')
        ax.axhline(ceil, color=col, lw=0.9, ls='--', alpha=0.5)
    ax.set_xscale('log', base=2)
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel('examples of the new job', fontsize=10)
    ax.set_ylabel('accuracy on the new job', fontsize=10)
    ax.set_ylim(0.45, 1.02)
    ax.set_title('A more varied job has a lower ceiling and a slower climb',
                 fontsize=11.2, weight='bold')
    ax.legend(fontsize=8.8, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _plain(ax2)
    needed = [n if n is not None else 1024 for n in d['needed']]  # type: ignore[union-attr]
    xx = np.arange(len(spreads))
    ax2.bar(xx, needed, color=cols, width=0.58)
    for x, (v, raw) in enumerate(zip(needed, d['needed'])):       # type: ignore[arg-type]
        txt = f'{v}' if raw is not None else 'more\nthan 512'
        ax2.text(x, v * 1.1, txt, ha='center', fontsize=9.6, color=INK, weight='bold')
    ax2.set_xticks(xx)
    ax2.set_xticklabels([f'{sp:.2f}' for sp in spreads], fontsize=10)
    ax2.set_xlabel('how widely the new job scatters', fontsize=10)
    ax2.set_yscale('log', base=2)
    ax2.set_yticks([32, 64, 128, 256, 512, 1024])
    ax2.set_yticklabels(['32', '64', '128', '256', '512', ''])
    ax2.set_ylim(32, 3000)
    ax2.set_ylabel('examples needed to come within 0.03 of the ceiling', fontsize=9.6)
    ax2.set_title('Twice the scatter, eight times the examples', fontsize=11.2,
                  weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    _save(fig, FT_DOC, 'data-vs-variation.svg')


# ==========================================================================
# PART 5.  The pictures for 04_making-a-model-smaller-and-faster.md
# ==========================================================================

def fig_memory_by_precision() -> None:
    """Section 1: the same model at four precisions, against two memory sizes."""
    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    names = [f'{n}\n{b:.2f} bits a weight' for n, b in PRECISIONS]
    vals = [_gib(TOTAL * b / 8) for _n, b in PRECISIONS]
    cols = [GRIP, WRIST, LINK, SLIDE]
    xx = np.arange(len(names))
    ax.bar(xx, vals, color=cols, width=0.56)
    for x, v in zip(xx, vals):
        ax.text(x, v + 0.5, f'{v:.2f} GiB', ha='center', fontsize=10.5, color=INK,
                weight='bold')
    ax.axhline(ROBOT_GIB, color=PURPLE, lw=2.0, ls='--')
    ax.text(3.45, ROBOT_GIB + 0.5, f'{ROBOT_GIB:.0f} GiB on a small robot computer',
            ha='right', fontsize=9.5, color=PURPLE)
    ax.axhline(CARD_GIB, color=TEAL, lw=2.0, ls=':')
    ax.text(3.45, CARD_GIB + 0.5, f'{CARD_GIB:.0f} GiB on a desktop graphics card',
            ha='right', fontsize=9.5, color=TEAL)
    ax.set_xticks(xx)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylabel('memory the weights alone need (GiB)', fontsize=10)
    ax.set_ylim(0, 29)
    ax.set_title(f'The same {_big(TOTAL)}-parameter model, stored four ways: only the '
                 f'4-bit version fits in {ROBOT_GIB:.0f} GiB with room to work',
                 fontsize=11.6, weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _save(fig, SM_DOC, 'memory-by-precision.svg')


def fig_bandwidth_tokens() -> None:
    """Section 1: generation speed is set by how many bytes have to be read."""
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.0), facecolor='white')
    _plain(ax)
    names = [n for n, _b in PRECISIONS]
    secs = [TOTAL * b / 8 / (BANDWIDTH_GBS * 1e9) for _n, b in PRECISIONS]
    cols = [GRIP, WRIST, LINK, SLIDE]
    xx = np.arange(len(names))
    ax.bar(xx, [1e3 * s for s in secs], color=cols, width=0.56)
    for x, s_ in zip(xx, secs):
        ax.text(x, 1e3 * s_ + 6, f'{1e3 * s_:.1f} ms', ha='center', fontsize=10.5,
                color=INK, weight='bold')
    ax.set_xticks(xx)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylabel('time to read every weight once (ms)', fontsize=10)
    ax.set_ylim(0, 310)
    ax.set_title(f'At {BANDWIDTH_GBS:.0f} GB a second', fontsize=11.2, weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _plain(ax2)
    toks = [1.0 / s_ for s_ in secs]
    ax2.bar(xx, toks, color=cols, width=0.56)
    for x, t in zip(xx, toks):
        ax2.text(x, t + 0.6, f'{t:.1f}', ha='center', fontsize=10.5, color=INK,
                 weight='bold')
    ax2.set_xticks(xx)
    ax2.set_xticklabels(names, fontsize=10)
    ax2.set_ylabel('words a second this allows, at best', fontsize=10)
    ax2.set_ylim(0, 33)
    ax2.set_title('Four bits is 7.5 times faster than float32, for the same arithmetic',
                  fontsize=11.2, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    fig.suptitle('Writing one word reads every weight once, so the size of the weights '
                 'sets the speed', fontsize=12.0, weight='bold', y=1.02)
    _save(fig, SM_DOC, 'bandwidth-tokens-per-second.svg')


def fig_latency_budget() -> None:
    """Section 1: what a control loop leaves for the model to think in."""
    rates = [5, 10, 30, 50]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.0), facecolor='white')
    _plain(ax)
    budgets = [1e3 / r for r in rates]
    xx = np.arange(len(rates))
    ax.bar(xx, budgets, color=[SLIDE, LINK, WRIST, GRIP], width=0.56)
    for x, b in zip(xx, budgets):
        ax.text(x, b + 4, f'{b:.0f} ms', ha='center', fontsize=10.5, color=INK,
                weight='bold')
    ax.set_xticks(xx)
    ax.set_xticklabels([f'{r} times\na second' for r in rates], fontsize=10)
    ax.set_ylabel('time for one decision (ms)', fontsize=10)
    ax.set_ylim(0, 230)
    ax.set_title('How often the arm asks for a new command', fontsize=11.2, weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _plain(ax2)
    toks = [(1.0 / r) * ACCEL_TFLOPS * 1e12 / FLOP_PER_TOKEN_FWD for r in rates]
    ax2.bar(xx, toks, color=[SLIDE, LINK, WRIST, GRIP], width=0.56)
    for x, t in zip(xx, toks):
        ax2.text(x, t + 6, f'{t:.0f} words', ha='center', fontsize=10.5, color=INK,
                 weight='bold')
    ax2.set_xticks(xx)
    ax2.set_xticklabels([f'{r} times\na second' for r in rates], fontsize=10)
    ax2.set_ylabel('words this model could write in that time', fontsize=10)
    ax2.set_ylim(0, 350)
    ax2.set_title(f'At a stated {ACCEL_TFLOPS:.0f} TFLOP a second and '
                  f'{FLOP_PER_TOKEN_FWD / 1e9:.1f} GFLOP a word', fontsize=11.2,
                  weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    fig.suptitle('A 30 Hz arm leaves 33 ms, which is about 49 words of this model and '
                 'nothing else', fontsize=12.0, weight='bold', y=1.02)
    _save(fig, SM_DOC, 'latency-budget.svg')


def fig_weights_and_levels() -> None:
    """Section 2: 48 real weights snapping onto 15 four-bit levels."""
    d = exp_weight_row()
    w = d['w']                               # type: ignore[index]
    scale4 = d['scale4']                     # type: ignore[index]
    fig, ax = plt.subplots(figsize=(12.2, 5.6), facecolor='white')
    _plain(ax)
    for k in range(-7, 8):
        ax.axhline(k * scale4, color=GRID, lw=0.8)        # type: ignore[operator]
        ax.text(-1.6, k * scale4, f'{k:+d}', va='center', ha='right', fontsize=8,
                color=MUTED)                              # type: ignore[operator]
    xs = np.arange(len(w))                                # type: ignore[arg-type]
    ax.vlines(xs, 0, w, color=LINK_PALE, lw=1.4)
    ax.plot(xs, w, 'o', color=LINK, ms=5, label='the weight as trained')
    ax.plot(xs, d['deq4'], 's', color=GRIP, ms=5,         # type: ignore[index]
            label='the weight read back from its 4-bit integer')
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlim(-3.5, len(w))                             # type: ignore[arg-type]
    ax.set_xlabel('one output channel of a trained weight matrix, weight by weight',
                  fontsize=10)
    ax.set_ylabel('weight', fontsize=10)
    ax.set_ylim(-0.63, 0.63)
    ax.set_title(f'The step between levels is {scale4:.5f}, so every weight has to move to '
                 f'the nearest line',                     # type: ignore[str-format]
                 fontsize=11.6, weight='bold')
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    _save(fig, SM_DOC, 'weights-and-levels.svg')


def fig_step_size() -> None:
    """Section 2: the number line, the step and the integers, 8 bits against 4."""
    d = exp_weight_row()
    w = d['w']                               # type: ignore[index]
    amax = float(np.abs(w).max())            # type: ignore[arg-type]
    fig, ax = plt.subplots(figsize=(12.4, 5.2), facecolor='white')
    _blank(ax)
    for row, (bits, col, y) in enumerate(((4, GRIP, 2.2), (8, LINK, 0.9))):
        qmax = 2 ** (bits - 1) - 1
        step = amax / qmax
        ax.plot([-amax, amax], [y, y], color=INK, lw=1.2)
        for k in range(-qmax, qmax + 1):
            ax.plot([k * step, k * step], [y - 0.09, y + 0.09], color=col,
                    lw=1.4 if bits == 4 else 0.35)
        ax.text(-amax - 0.03, y, f'{bits} bits', ha='right', va='center', fontsize=11,
                color=col, weight='bold')
        ax.text(0, y + 0.3, f'{2 * qmax + 1} levels, one every {step:.6f}',
                ha='center', fontsize=9.6, color=col)
        ax.text(-amax, y - 0.28, f'{-qmax}', ha='center', fontsize=9, color=MUTED)
        ax.text(amax, y - 0.28, f'+{qmax}', ha='center', fontsize=9, color=MUTED)
        ax.text(0, y - 0.28, '0', ha='center', fontsize=9, color=MUTED)
    sample = w[:1]                                        # type: ignore[index]
    for v in w[:6]:                                       # type: ignore[index]
        ax.plot([v], [2.2], 'v', color=PURPLE, ms=8)
        ax.plot([v], [0.9], 'v', color=PURPLE, ms=8)
    ax.text(0.0, 3.0, 'The purple arrows are the first six real weights from the same '
                      'column. At 8 bits each lands almost on a line; at 4 bits it has '
                      'to move.', ha='center', fontsize=9.6, color=PURPLE)
    ax.set_xlim(-amax * 1.22, amax * 1.12)
    ax.set_ylim(0.2, 3.4)
    ax.set_title(f'The same range, {-amax:.4f} to {amax:.4f}, cut into 255 steps or into 15',
                 fontsize=11.8, weight='bold')
    _save(fig, SM_DOC, 'step-size-number-line.svg')


def fig_error_per_weight() -> None:
    """Section 2: the error left on each weight at 8 bits and at 4."""
    d = exp_weight_row()
    w = d['w']                               # type: ignore[index]
    xs = np.arange(len(w))                   # type: ignore[arg-type]
    e8 = np.asarray(d['deq8']) - w           # type: ignore[index]
    e4 = np.asarray(d['deq4']) - w           # type: ignore[index]
    fig, ax = plt.subplots(figsize=(12.2, 5.2), facecolor='white')
    _plain(ax)
    ax.bar(xs - 0.2, e4, width=0.4, color=GRIP, label='4 bits')
    ax.bar(xs + 0.2, e8, width=0.4, color=LINK, label='8 bits')
    ax.axhline(d['rms4'], color=GRIP, lw=1.2, ls='--')    # type: ignore[index]
    ax.axhline(-d['rms4'], color=GRIP, lw=1.2, ls='--')   # type: ignore[index]
    ax.set_ylim(-0.055, 0.060)
    ax.text(0.0, 0.050,                                   # type: ignore[index]
            f'root-mean-square error at 4 bits: {d["rms4"]:.6f}', ha='left', fontsize=9.3,
            color=GRIP,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))
    ax.axhline(d['rms8'], color=LINK, lw=1.2, ls=':')     # type: ignore[index]
    ax.text(0, -0.049,                                    # type: ignore[index]
            f'at 8 bits it is {d["rms8"]:.6f}, which is '
            f'{d["rms4"] / d["rms8"]:.0f} times smaller', fontsize=9.3, color=LINK,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlabel('weight number', fontsize=10)
    ax.set_ylabel('read-back value minus the trained value', fontsize=10)
    ax.set_xlim(-1, len(w))                               # type: ignore[arg-type]
    ax.set_title('Four bits leaves an error on every weight; eight bits leaves almost none',
                 fontsize=11.8, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, SM_DOC, 'error-per-weight.svg')


def fig_error_vs_bits() -> None:
    """Section 2: every extra bit halves the error."""
    d = exp_weight_row()
    bits = d['bit_list']                     # type: ignore[index]
    errs = d['rms_list']                     # type: ignore[index]
    fig, ax = plt.subplots(figsize=(10.4, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(bits, errs, marker='o', color=LINK, lw=2.4, ms=7)
    for b, e in zip(bits, errs):             # type: ignore[arg-type]
        ax.annotate(f'{e:.6f}', xy=(b, e), xytext=(b + 0.12, e * 1.35), fontsize=9.2,
                    color=INK)
    ax.set_yscale('log')
    ax.set_xticks(bits)
    ax.set_xlabel('bits kept for each weight', fontsize=10)
    ax.set_ylabel('root-mean-square error left in the weights (log scale)', fontsize=10)
    ax.set_xlim(1.5, 11.2)
    ax.set_ylim(2e-4, 0.40)
    ax.set_title('Each extra bit halves the step and so halves the error, which is why '
                 '8 bits is nearly free and 4 is not',
                 fontsize=11.6, weight='bold')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, SM_DOC, 'error-vs-bits.svg')


def fig_per_channel_scales() -> None:
    """Section 3: one scale for a whole matrix wastes most of the levels."""
    d = exp_per_channel()
    w = d['w']                               # type: ignore[index]
    loud = d['loud']                         # type: ignore[index]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12.0, 6.4), facecolor='white',
                                  sharex=True)
    for a, mat, label, col in ((ax, w, 'the matrix as trained', LINK),
                               (ax2, loud, 'the same matrix with one loud channel', WRIST)):
        _plain(a)
        amax_col = np.abs(mat).max(axis=0)
        a.bar(np.arange(len(amax_col)), amax_col, color=col, width=0.72)
        a.axhline(float(np.abs(mat).max()), color=GRIP, lw=1.8, ls='--')
        a.text(47.4, float(np.abs(mat).max()) * 0.97,
               f'one scale for the whole matrix is set by {np.abs(mat).max():.3f}',
               ha='right', va='top', fontsize=9.3, color=GRIP)
        a.set_ylabel('largest weight\nin that channel', fontsize=9.6)
        a.set_title(label, fontsize=11.0, weight='bold')
        a.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
        a.set_axisbelow(True)
    ax2.set_xlabel('output channel of a real 48 x 48 trained weight matrix', fontsize=10)
    ax2.set_xlim(-0.8, 48)
    fig.suptitle('A scale per channel follows each bar; a scale for the whole matrix '
                 'follows only the tallest',
                 fontsize=12.0, weight='bold', y=1.0)
    _save(fig, SM_DOC, 'per-channel-scales.svg')


def fig_scale_choice_error() -> None:
    """Section 3: what each choice of scale leaves behind, measured."""
    d = exp_per_channel()
    fig, ax = plt.subplots(figsize=(11.2, 5.4), facecolor='white')
    _plain(ax)
    modes = ['per-tensor', 'per-channel', 'grouped']
    nice = ['one scale for\nthe whole matrix', 'one scale for\neach channel',
            'one scale for\nevery 16 weights']
    xx = np.arange(3)
    for k, (label, col, off) in enumerate((('as trained', LINK, -0.2),
                                           ('with one loud channel', GRIP, 0.2))):
        vals = [100.0 * d[label][f'{m}4'] for m in modes]       # type: ignore[index]
        ax.bar(xx + off, vals, width=0.36, color=col, label=f'4 bits, {label}')
        for x, v in zip(xx, vals):
            ax.text(x + off, v + 1.0, f'{v:.1f}%', ha='center', fontsize=9.6, color=INK)
    ax.set_xticks(xx)
    ax.set_xticklabels(nice, fontsize=10)
    ax.set_ylabel('error left in the weights, as a share of their own size (%)',
                  fontsize=10)
    ax.set_ylim(0, 60)
    ax.set_title('One loud channel ruins a single scale, and a scale per channel does not '
                 'notice it', fontsize=11.8, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='upper right')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _save(fig, SM_DOC, 'scale-choice-error.svg')


def fig_ptq_vs_qat() -> None:
    """Section 3: quantising after training against training with it in mind."""
    d = exp_ptq_qat()
    bits = d['bits']                         # type: ignore[index]
    fig, ax = plt.subplots(figsize=(10.8, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(bits, d['ptq'], marker='o', color=LINK, lw=2.4, ms=7,   # type: ignore[arg-type]
            label='trained first, then squeezed')
    ax.plot(bits, d['qat'], marker='s', color=SLIDE, lw=2.4, ms=7,  # type: ignore[arg-type]
            label='trained with the squeezing switched on')
    ax.axhline(d['float'], color=GRIP, lw=1.8, ls='--')             # type: ignore[arg-type]
    ax.text(8.1, d['float'] + 0.006, f'the full-precision network: {d["float"]:.3f}',
            ha='right', fontsize=9.5, color=GRIP)
    for b, p, q in zip(bits, d['ptq'], d['qat']):                   # type: ignore[arg-type]
        if b <= 3:
            ax.annotate(f'{p:.3f}', xy=(b, p), xytext=(b - 0.08, p - 0.028),
                        fontsize=9.2, color=LINK, ha='center')
            ax.annotate(f'{q:.3f}', xy=(b, q), xytext=(b - 0.08, q + 0.014),
                        fontsize=9.2, color=SLIDE, ha='center')
    ax.set_xticks(bits)
    ax.set_xlabel('bits kept for each weight', fontsize=10)
    ax.set_ylabel('accuracy on the six-way test set', fontsize=10)
    ax.set_ylim(0.80, 0.958)
    ax.set_title('Down to three bits it makes no difference; at two bits, training with '
                 'the squeezing on wins back 0.086',
                 fontsize=11.6, weight='bold')
    ax.legend(fontsize=9.8, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, SM_DOC, 'ptq-vs-qat.svg')


def fig_mode_accuracy() -> None:
    """Section 3: the choice of scale, measured as accuracy rather than error."""
    d = exp_ptq_qat()
    bits = d['bits']                         # type: ignore[index]
    modes = d['modes']                       # type: ignore[index]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.0), facecolor='white')
    _plain(ax)
    for (name, vals), col, mk in zip(modes.items(), (GRIP, LINK, SLIDE), ('o', 's', '^')):
        nice = {'per-tensor': 'one scale for the whole matrix',
                'per-channel': 'one scale for each channel',
                'grouped': 'one scale for every 16 weights'}[name]
        ax.plot(bits, vals, marker=mk, color=col, lw=2.2, ms=6.5, label=nice)
    ax.axhline(d['float'], color=MUTED, lw=1.4, ls='--')            # type: ignore[arg-type]
    ax.set_xticks(bits)
    ax.set_xlabel('bits kept for each weight', fontsize=10)
    ax.set_ylabel('accuracy on the six-way test set', fontsize=10)
    ax.set_ylim(0.6, 0.97)
    ax.set_title('Where the scale starts to matter', fontsize=11.2, weight='bold')
    ax.legend(fontsize=9.3, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _plain(ax2)
    clips = d['clips']                       # type: ignore[index]
    names = [c[0] for c in clips]
    vals = [c[1] for c in clips]
    xx = np.arange(len(names))
    ax2.bar(xx, vals, color=[LINK, TEAL, WRIST, GRIP], width=0.58)
    for x, v in zip(xx, vals):
        ax2.text(x, v + 0.0015, f'{v:.3f}', ha='center', fontsize=10.2, color=INK,
                 weight='bold')
    ax2.set_xticks(xx)
    ax2.set_xticklabels([n.replace(' ', '\n') for n in names], fontsize=9.3)
    ax2.set_ylabel('accuracy at 4 bits, one scale per channel', fontsize=10)
    ax2.set_ylim(0.90, 0.945)
    ax2.set_title('Where the range is cut off, at 4 bits', fontsize=11.2, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    _save(fig, SM_DOC, 'scale-and-clipping-accuracy.svg')


def fig_soft_target() -> None:
    """Section 4: one example, the hard label and the teacher's whole answer."""
    d = exp_distil()
    rows = d['rows']                         # type: ignore[index]
    p1 = rows[1.0]
    true = d['true']                         # type: ignore[index]
    ent = d['ent']                           # type: ignore[index]
    labels = [f'class {i}' for i in range(N_CLASS)]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.6, 5.0), facecolor='white')
    _plain(ax)
    hard = np.zeros(N_CLASS)
    hard[true] = 1.0
    xx = np.arange(N_CLASS)
    ax.bar(xx, hard, color=MUTED, width=0.6)
    for x, v in zip(xx, hard):
        ax.text(x, v + 0.02, f'{v:.0f}', ha='center', fontsize=10.5, color=INK)
    ax.set_xticks(xx)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel('what the student is told to aim at', fontsize=10)
    ax.set_title('The hard label: one right answer and five zeros\n'
                 '(it carries 0.000 bits beyond the name of the class)',
                 fontsize=11.0, weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _plain(ax2)
    ax2.bar(xx, p1, color=LINK, width=0.6)
    for x, v in zip(xx, p1):
        ax2.text(x, v + 0.02, f'{v:.3f}', ha='center', fontsize=10.0, color=INK)
    ax2.set_xticks(xx)
    ax2.set_xticklabels(labels, fontsize=9.5)
    ax2.set_ylim(0, 1.12)
    ax2.set_ylabel('what the student is told to aim at', fontsize=10)
    ax2.set_title(f'The teacher\'s whole answer on the same example\n'
                  f'(it carries {ent[1.0]:.3f} bits, and it says class 0 is the near miss)',
                  fontsize=11.0, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    fig.suptitle(f'One example whose true class is {true}: the teacher is sure, but not '
                 f'blind to the alternative', fontsize=12.0, weight='bold', y=1.02)
    _save(fig, SM_DOC, 'soft-target-one-example.svg')


def fig_temperature() -> None:
    """Section 4: temperature flattens the answer and lets the small numbers speak."""
    d = exp_distil()
    rows = d['rows']                         # type: ignore[index]
    ent = d['ent']                           # type: ignore[index]
    temps = sorted(rows)
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.0), facecolor='white',
                                  gridspec_kw={'width_ratios': [1.45, 1.0]})
    _plain(ax)
    width = 0.15
    cols = [TEAL, SLIDE, LINK, WRIST, GRIP]
    xx = np.arange(N_CLASS)
    for k, (t, col) in enumerate(zip(temps, cols)):
        ax.bar(xx + (k - 2) * width, rows[t], width=width, color=col,
               label=f'temperature {t:.0f}')
    ax.set_xticks(xx)
    ax.set_xticklabels([f'class {i}' for i in range(N_CLASS)], fontsize=9.5)
    ax.set_ylabel('the number the student aims at', fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.set_title('The same example at five temperatures', fontsize=11.2, weight='bold')
    ax.legend(fontsize=9.3, frameon=False, loc='upper center', ncol=3)
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _plain(ax2)
    ax2.plot(temps, [ent[t] for t in temps], marker='o', color=PURPLE, lw=2.4, ms=7)
    for t in temps:
        ax2.annotate(f'{ent[t]:.3f}', xy=(t, ent[t]), xytext=(t + 0.12, ent[t] - 0.09),
                     fontsize=9.3, color=INK)
    ax2.set_xlabel('temperature', fontsize=10)
    ax2.set_ylabel('information in the answer (bits)', fontsize=10)
    ax2.set_ylim(0, 1.6)
    ax2.set_xlim(0, 9)
    ax2.set_title('A warmer answer carries more', fontsize=11.2, weight='bold')
    ax2.grid(color=GRID, lw=0.6, alpha=0.6)
    ax2.set_axisbelow(True)
    _save(fig, SM_DOC, 'temperature-sweep.svg')


def fig_student_curves() -> None:
    """Section 4: the same student, taught two ways."""
    d = exp_distil()
    ns = d['ns']                             # type: ignore[index]
    fig, ax = plt.subplots(figsize=(10.8, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(ns, d['hard'], marker='o', color=MUTED, lw=2.4, ms=7,   # type: ignore[arg-type]
            label='the student taught with hard labels only')
    ax.plot(ns, d['soft'], marker='s', color=LINK, lw=2.4, ms=7,    # type: ignore[arg-type]
            label="the student taught with the teacher's whole answer, temperature 3")
    ax.axhline(d['teacher_acc'], color=GRIP, lw=1.8, ls='--')       # type: ignore[arg-type]
    ax.text(640, d['teacher_acc'] + 0.006, f'the teacher: {d["teacher_acc"]:.3f}',
            ha='right', fontsize=9.5, color=GRIP)
    for n, h, s_ in zip(ns, d['hard'], d['soft']):                  # type: ignore[arg-type]
        if n in (20, 40):
            ax.annotate(f'{s_ - h:+.3f}', xy=(n, (h + s_) / 2), xytext=(n * 1.12,
                        (h + s_) / 2 - 0.034), fontsize=9.4, color=SLIDE, weight='bold')
    ax.set_xscale('log', base=2)
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel('examples the student is shown', fontsize=10)
    ax.set_ylabel(f'accuracy of the student (mean of 5 runs)', fontsize=10)
    ax.set_ylim(0.52, 0.97)
    ax.set_title('The teacher\'s whole answer is worth most when examples are few, and '
                 'nothing at all when they are many',
                 fontsize=11.6, weight='bold')
    ax.legend(fontsize=9.6, frameon=False, loc='lower right')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, SM_DOC, 'student-against-hard-labels.svg')


def fig_teacher_student_size() -> None:
    """Section 4: what the student actually saves."""
    d = exp_distil()
    t = big()
    sizes = d['student_sizes']               # type: ignore[index]
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.6), facecolor='white')
    pairs = [('parameters', [t.n_param, d['n_student']]),
             ('multiply-adds for\none decision', [t.macs, macs(sizes)]),
             ('accuracy on the\nsix-way test set', [t.acc, d['soft'][-1]])]   # type: ignore
    for ax, (label, vals) in zip(axes, pairs):
        _plain(ax)
        ax.bar([0, 1], vals, color=[GRIP, LINK], width=0.5)
        for x, v in zip([0, 1], vals):
            txt = f'{v:.3f}' if v < 2 else f'{v:,.0f}'
            ax.text(x, v * 1.03 if v > 2 else v + 0.012, txt, ha='center', fontsize=11,
                    color=INK, weight='bold')
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f'teacher\n{t.sizes}', f'student\n{sizes}'], fontsize=9.5)
        ax.set_ylabel(label, fontsize=10)
        if v > 2:
            ax.set_ylim(0, max(vals) * 1.22)
        else:
            ax.set_ylim(0.8, 1.0)
        ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)
    fig.suptitle(f'The student holds {t.n_param / d["n_student"]:.0f} times fewer numbers '
                 f'and does {t.macs / macs(sizes):.0f} times less arithmetic, and it has '
                 f'given up {t.acc - d["soft"][-1]:.3f} of accuracy',
                 fontsize=12.0, weight='bold', y=1.03)
    _save(fig, SM_DOC, 'teacher-and-student-size.svg')


def fig_prune_masks() -> None:
    """Section 5: scattered zeros leave the shape alone; whole neurons shrink it."""
    b = big()
    w = b.w[1][:24, :24]
    vmax = float(np.abs(w).max())
    thresh = np.quantile(np.abs(w).ravel(), 0.5)
    scattered = np.where(np.abs(w) >= thresh, np.abs(w), np.nan)
    keep_cols = np.sort(np.argsort(-np.linalg.norm(w, axis=0))[:12])
    narrow = np.abs(w[:, keep_cols])
    fig, axes = plt.subplots(1, 3, figsize=(13.4, 5.0), facecolor='white')
    panels = [('every weight kept', np.abs(w), 24, f'{24 * 24:,} multiply-adds',
               'shape 24 x 24'),
              ('half the weights set to zero,\nwherever they happen to be', scattered, 24,
               f'{24 * 24:,} multiply-adds on\nordinary hardware', 'shape still 24 x 24'),
              ('half the output channels\ntaken out completely', narrow, 12,
               f'{24 * 12:,} multiply-adds, truly', 'shape now 24 x 12')]
    for ax, (title, mat, width, cost, shape) in zip(axes, panels):
        _blank(ax)
        ax.imshow(mat, cmap='Blues', vmin=0, vmax=vmax, interpolation='nearest',
                  extent=(0.0, float(width), 24.0, 0.0))
        ax.add_patch(Rectangle((0, 0), width, 24, facecolor='none', edgecolor=INK, lw=1.2))
        ax.set_xlim(0, 24)
        ax.set_ylim(31.5, -1.0)
        ax.set_title(title, fontsize=10.6, weight='bold')
        ax.text(12, 25.6, cost, ha='center', va='top', fontsize=9.6, color=INK)
        ax.text(12, 29.6, shape, ha='center', va='top', fontsize=9.2, color=MUTED)
    fig.suptitle('A hole in a matrix is still a matrix: only taking whole channels out '
                 'makes the multiplication smaller',
                 fontsize=12.0, weight='bold', y=1.02)
    _save(fig, SM_DOC, 'scattered-zeros-against-whole-channels.svg')


def fig_prune_accuracy() -> None:
    """Section 5: accuracy as weights are removed, two ways."""
    d = exp_prune()
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor='white')
    _plain(ax)
    sp = [100 * v for v in d['sparsities']]            # type: ignore[union-attr]
    ax.plot(sp, d['uns'], marker='o', color=LINK, lw=2.4, ms=6,   # type: ignore[arg-type]
            label='smallest weights set to zero, wherever they are')
    ax.plot([50], [d['two_four']], '*', color=WRIST, ms=18)       # type: ignore[index]
    ax.annotate(f'2 of every 4 kept: {d["two_four"]:.3f}', xy=(50, d['two_four']),
                xytext=(14, 0.80), fontsize=9.6, color=WRIST,
                arrowprops=dict(arrowstyle='-|>', color=WRIST, lw=1.2))
    ax.axhline(d['base_acc'], color=GRIP, lw=1.6, ls='--')        # type: ignore[arg-type]
    ax.text(0, d['base_acc'] + 0.015, f'the full network: {d["base_acc"]:.3f}',
            fontsize=9.5, color=GRIP)
    for x, v in zip(sp, d['uns']):                                # type: ignore[arg-type]
        if x in (70.0, 80.0, 90.0):
            ax.annotate(f'{v:.3f}', xy=(x, v), xytext=(x - 2.0, v - 0.07), fontsize=9.2,
                        color=LINK)
    ax.set_xlabel('share of the weights set to zero (%)', fontsize=10)
    ax.set_ylabel('accuracy on the six-way test set', fontsize=10)
    ax.set_ylim(0.1, 1.02)
    ax.set_title('Half the weights can go without being noticed', fontsize=11.2,
                 weight='bold')
    ax.legend(fontsize=9.4, frameon=False, loc='lower left')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _plain(ax2)
    saved = [100 * v for v in d['stru_sparsity']]     # type: ignore[union-attr]
    ax2.plot(saved, d['stru'], marker='s', color=SLIDE, lw=2.4, ms=6,  # type: ignore
             label='whole hidden neurons removed')
    ax2.plot([0], [d['base_acc']], 'o', color=GRIP, ms=8)              # type: ignore[index]
    for x, v, k, mc in zip(saved, d['stru'], d['keeps'], d['stru_macs']):   # type: ignore
        if k in (40, 32, 24, 16, 8):
            ax2.annotate(f'{k} kept\n{mc:,} multiply-adds', xy=(x, v),
                         xytext=(x - 3.0, v - 0.13), fontsize=8.8, color=INK, ha='center')
    ax2.axhline(d['base_acc'], color=GRIP, lw=1.6, ls='--')            # type: ignore[arg-type]
    ax2.set_xlabel('arithmetic actually saved (%)', fontsize=10)
    ax2.set_ylabel('accuracy on the six-way test set', fontsize=10)
    ax2.set_ylim(0.1, 1.02)
    ax2.set_xlim(-4, 100)
    ax2.set_title('Arithmetic you can really save costs more accuracy', fontsize=11.2,
                  weight='bold')
    ax2.legend(fontsize=9.4, frameon=False, loc='lower left')
    ax2.grid(color=GRID, lw=0.6, alpha=0.6)
    ax2.set_axisbelow(True)
    _save(fig, SM_DOC, 'accuracy-against-pruning.svg')


def fig_two_of_four() -> None:
    """Section 5: the 2:4 pattern on four real weights."""
    b = big()
    d = exp_prune()
    w = b.w[1][:12, 0]
    fig, ax = plt.subplots(figsize=(12.2, 4.8), facecolor='white')
    _blank(ax)
    for g in range(3):
        vals = w[g * 4:(g + 1) * 4]
        order = np.argsort(-np.abs(vals))
        keep = set(order[:2].tolist())
        for i, v in enumerate(vals):
            x = g * 4.6 + i * 1.05
            kept = i in keep
            ax.add_patch(Rectangle((x, 0.6), 0.92, 0.9,
                                   facecolor=LINK if kept else '#eeeeee',
                                   edgecolor=INK if kept else '#bbbbbb', lw=1.0))
            ax.text(x + 0.46, 1.05, f'{v:+.3f}', ha='center', va='center', fontsize=10,
                    color='white' if kept else MUTED)
            ax.text(x + 0.46, 0.4, 'kept' if kept else 'set to 0', ha='center', fontsize=8.6,
                    color=LINK if kept else MUTED)
        ax.text(g * 4.6 + 2.0, 1.78, f'group {g + 1} of four weights', ha='center',
                fontsize=9.6, color=INK)
    ax.text(6.9, -0.35,
            f'Half of every group of four is dropped, which is a pattern the hardware can '
            f'skip, and it leaves {d["two_four"]:.3f} accuracy against '
            f'{d["uns"][3]:.3f} when the same share of weights is dropped freely.',
            ha='center', fontsize=9.8, color=INK)
    ax.set_xlim(-0.4, 14.0)
    ax.set_ylim(-0.8, 2.2)
    ax.set_title('2:4 sparsity: in every run of four weights, the two smallest go',
                 fontsize=11.8, weight='bold')
    _save(fig, SM_DOC, 'two-of-four-pattern.svg')


def fig_accuracy_against_saving() -> None:
    """Section 6: every method as one point, measured on the same network."""
    s = sim()
    b = big()
    d = exp_prune()
    pq = exp_ptq_qat()
    dist = exp_distil()
    st = exp_stack()
    base_bytes = b.n_param * 2.0
    pts: list[tuple[str, float, float, str]] = []
    pts.append(('8-bit weights', pq['ptq'][0], base_bytes / (b.n_param * 1.0), LINK))
    pts.append(('4-bit weights', pq['ptq'][3], base_bytes / (b.n_param * 0.5), TEAL))
    pts.append(('2-bit weights,\nquantisation-aware', pq['qat'][5],
                base_bytes / (b.n_param * 0.25), SLIDE))
    pts.append(('half the weights\nzeroed freely', d['uns'][3], 1.0, MUTED))
    pts.append(('2 of every 4 kept', d['two_four'], 2.0, WRIST))
    pts.append(('32 of 48 neurons kept', d['stru'][2],
                base_bytes / (sum(a * c + c for a, c in zip([FEAT, 32, 32],
                                                            [32, 32, N_CLASS])) * 2.0),
                PURPLE))
    pts.append(('distilled student', dist['soft'][-1],
                base_bytes / (dist['n_student'] * 2.0), GRIP))
    pts.append(('distilled student,\n4-bit weights', dist['q4'],
                base_bytes / (dist['n_student'] * 0.5), INK))
    fig, ax = plt.subplots(figsize=(11.4, 5.8), facecolor='white')
    _plain(ax)
    for name, acc, save, col in pts:
        ax.plot([save], [b.acc - acc], 'o', color=col, ms=11)
        dy = -0.0085 if (b.acc - acc) > 0.05 else 0.004
        ax.annotate(name, xy=(save, b.acc - acc), xytext=(save * 1.07, b.acc - acc + dy),
                    fontsize=9.3, color=col, va='top' if dy < 0 else 'bottom')
    ax.axhline(0.0, color=INK, lw=1.0)
    ax.set_ylim(-0.006, 0.070)
    ax.text(11.0, 0.0012, 'no accuracy lost at all', fontsize=9.3, color=INK)
    ax.set_xscale('log', base=2)
    ax.set_xticks([1, 2, 4, 8, 16, 32, 64, 128])
    ax.set_xticklabels(['1', '2', '4', '8', '16', '32', '64', '128'])
    ax.set_xlim(0.85, 330)
    ax.set_xlabel('times smaller than the trained network (log scale)', fontsize=10)
    ax.set_ylabel('accuracy given up', fontsize=10)
    best = pts[-1]
    lost = round(b.acc, 3) - round(best[1], 3)
    ax.set_title(f'Measured on the same small network: a distilled student squeezed to 4 '
                 f'bits is {best[2]:.0f} times smaller for {lost:.3f} '
                 f'of accuracy', fontsize=11.6, weight='bold')
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    _save(fig, SM_DOC, 'accuracy-lost-against-size-saved.svg')


def fig_summary_table() -> None:
    """Section 6: the whole page as one table of measured numbers."""
    b = big()
    d = exp_prune()
    pq = exp_ptq_qat()
    dist = exp_distil()
    st = exp_stack()

    def gap(a: float) -> str:
        return f'{round(b.acc, 3) - round(a, 3):+.3f}'

    rows = [
        ('8-bit weights, a scale per channel', f'{pq["ptq"][0]:.3f}', gap(pq['ptq'][0]),
         '2 times', '2 times', 'measured'),
        ('4-bit weights, a scale per channel', f'{pq["ptq"][3]:.3f}', gap(pq['ptq'][3]),
         '4 times', '4 times', 'measured'),
        ('2-bit weights, trained for it', f'{pq["qat"][5]:.3f}', gap(pq['qat'][5]),
         '8 times', '8 times', 'measured'),
        ('half the weights zeroed freely', f'{d["uns"][3]:.3f}', gap(d['uns'][3]),
         'none on ordinary\nhardware', 'none', 'measured'),
        ('2 of every 4 weights kept', f'{d["two_four"]:.3f}', gap(d['two_four']),
         '2 times, if the\nhardware knows', 'up to 2 times', 'measured, saving\nillustrative'),
        ('32 of 48 hidden neurons kept', f'{d["stru"][2]:.3f}', gap(d['stru'][2]),
         '2.0 times', '2.0 times', 'measured'),
        ('distilled into a smaller student', f'{dist["soft"][-1]:.3f}',
         gap(dist['soft'][-1]), '20.7 times', '22.0 times', 'measured'),
        ('distilled, then squeezed to 4 bits', f'{dist["q4"]:.3f}',
         gap(dist['q4']), '82.8 times', '22.0 times', 'measured'),
    ]
    fig, ax = plt.subplots(figsize=(13.6, 5.8), facecolor='white')
    _blank(ax)
    heads = ['what was done', 'accuracy', 'accuracy\ngiven up', 'memory\nsaved',
             'arithmetic\nsaved', 'where the number\ncomes from']
    xs = [0.015, 0.355, 0.445, 0.555, 0.685, 0.810]
    for x, h in zip(xs, heads):
        ax.text(x, 0.99, h, fontsize=9.8, color=MUTED, weight='bold', va='top')
    ax.plot([0.0, 1.0], [0.875, 0.875], color=INK, lw=1.0)
    for i, row in enumerate(rows):
        y = 0.815 - i * 0.100
        if i % 2 == 0:
            ax.add_patch(Rectangle((0.0, y - 0.050), 1.0, 0.096, facecolor='#f6f6f6',
                                   edgecolor='none'))
        for x, cell in zip(xs, row):
            ax.text(x, y, cell, fontsize=9.4, color=INK, va='center')
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(f'Every row measured on the same {b.n_param:,}-parameter network, whose '
                 f'own accuracy is {b.acc:.3f}',
                 fontsize=11.8, weight='bold')
    _save(fig, SM_DOC, 'method-summary-table.svg')


def fig_stack_methods() -> None:
    """Section 6: the methods are not alternatives, they stack."""
    st = exp_stack()
    rows = st['rows']                        # type: ignore[index]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.2), facecolor='white')
    names = [r[0].replace(', ', '\n').replace(' a weight', '') for r in rows]
    accs = [r[1] for r in rows]
    bytes_ = [r[2] for r in rows]
    cols = [GRIP, WRIST, LINK, TEAL, SLIDE]
    xx = np.arange(len(rows))
    _plain(ax)
    ax.bar(xx, bytes_, color=cols, width=0.58)
    ax.set_yscale('log')
    for x, v in zip(xx, bytes_):
        ax.text(x, v * 1.25, f'{v:,.0f} bytes', ha='center', fontsize=9.6, color=INK)
    ax.set_xticks(xx)
    ax.set_xticklabels(names, fontsize=8.8)
    ax.set_ylabel('bytes of weights (log scale)', fontsize=10)
    ax.set_ylim(30, 4e4)
    ax.set_title('What the weights take up', fontsize=11.2, weight='bold')
    ax.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    _plain(ax2)
    ax2.bar(xx, accs, color=cols, width=0.58)
    for x, v in zip(xx, accs):
        ax2.text(x, v + 0.0015, f'{v:.3f}', ha='center', fontsize=10, color=INK,
                 weight='bold')
    ax2.set_xticks(xx)
    ax2.set_xticklabels(names, fontsize=8.8)
    ax2.set_ylabel('accuracy on the six-way test set', fontsize=10)
    ax2.set_ylim(0.90, 0.945)
    ax2.set_title('What it costs in accuracy', fontsize=11.2, weight='bold')
    ax2.grid(axis='y', color=GRID, lw=0.6, alpha=0.7)
    ax2.set_axisbelow(True)
    fig.suptitle(f'Distilling and then quantising gives '
                 f'{rows[0][2] / rows[4][2]:.0f} times smaller weights for '
                 f'{round(rows[0][1], 3) - round(rows[4][1], 3):.3f} of accuracy',
                 fontsize=12.0, weight='bold', y=1.02)
    _save(fig, SM_DOC, 'distil-then-quantise.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    report_shape()
    report_prompt_cost()
    report_lora()
    report_qlora()
    report_fit()
    sim()
    big()
    fig_rungs_what_moves()
    fig_rung_trainable_bars()
    fig_prompt_cost_crossover()
    fig_bytes_you_ship()
    fig_model_shape()
    fig_bytes_per_parameter()
    fig_memory_per_rung()
    fig_unfreeze_blocks()
    fig_lora_two_thin_matrices()
    fig_lora_rank_counts()
    fig_lora_where()
    fig_lora_scaling_folding()
    fig_qlora_memory()
    fig_qlora_groups()
    fig_qlora_recovers()
    fig_forgetting_curves()
    fig_forgetting_what_helps()
    fig_forgetting_mix()
    fig_forgetting_frontier()
    fig_data_curves()
    fig_data_distance()
    fig_data_variation()
    fig_memory_by_precision()
    fig_bandwidth_tokens()
    fig_latency_budget()
    fig_weights_and_levels()
    fig_step_size()
    fig_error_per_weight()
    fig_error_vs_bits()
    fig_per_channel_scales()
    fig_scale_choice_error()
    fig_ptq_vs_qat()
    fig_mode_accuracy()
    fig_soft_target()
    fig_temperature()
    fig_student_curves()
    fig_teacher_student_size()
    fig_prune_masks()
    fig_prune_accuracy()
    fig_two_of_four()
    fig_accuracy_against_saving()
    fig_summary_table()
    fig_stack_methods()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
