"""Generate the diagrams for one page of docs/05_neural-networks/13_starting-your-own-model/.

    03_what-to-reuse-and-what-to-train.md
        -> images/starting-your-own-model/what-to-reuse-and-what-to-train/

Run with:  python3 docs/diagrams/starting_your_own_model_3.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints all of them so the document can quote the same values.

Three kinds of number appear here.

The parameter counts, the adapter counts, the memory sizes and the
floating-point operation counts are exact arithmetic on one stated picture
model: a transformer over picture patches, 224 by 224 pixels cut into 16 by 16
patches, so 197 tokens, with 12 blocks, a width of 768, a feed-forward inner
width of 3072 and a six-way head. The same arithmetic is also run on the
stated 7 thousand million parameter language model of
docs/05_neural-networks/07_pretraining-and-adapting/, for contrast. The
arithmetic rate of the two machines, the rent, the human minutes per picture
and per demonstration and the human hours per project stage are stated
assumptions, and the pictures and the page say so.

The learning experiments are simulated. Each example is 200 numbers standing in
for one look at one object: a fixed random mixture of 16 hidden numbers, 6 of
them part strengths and 10 of them nuisance, put through a cosine, drawn with
numpy.random.default_rng. A small fully connected network (200 to 48 to 24 to
6) is pretrained on a six-class source job in NumPy. The six rungs of the
ladder are then run on that network for real: using it as it is, picking the
best fixed mapping of its existing classes, training a new head on its frozen
features, training a rank-2 low-rank adapter, fine-tuning everything, and
training the same shape from a random start. The candidate-backbone experiment
pretrains eight such networks on eight different source jobs and measures what
each one is worth on one target job. The methods are real; only the data is
made up.

scipy is used for the correlation coefficients.
"""

import os
import pathlib
import sys

# The matrices in the simulated experiments are small, so splitting one
# multiply across cores costs far more than it saves. These have to be set
# before numpy is imported, because that is when the library reads them.
for _var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_var, '1')

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402
from scipy import stats  # noqa: E402

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

DOC: str = 'what-to-reuse-and-what-to-train'

Arr = NDArray[np.float64]
Ints = NDArray[np.int64]


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


def _blank(ax: Axes) -> None:
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ('top', 'right', 'bottom', 'left'):
        ax.spines[side].set_visible(False)


def _softmax(z: Arr) -> Arr:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _human(n: float) -> str:
    """A count with thousands separators, for drawing on a picture."""
    return f'{int(round(n)):,}'


# ==========================================================================
# PART ONE: exact arithmetic on the stated shapes
# ==========================================================================

IMG: int = 224
PATCH: int = 16
WIDTH: int = 768
BLOCKS: int = 12
FF: int = 3072
TOKENS: int = (IMG // PATCH) ** 2 + 1          # 196 patches plus one summary token
JOB_CLASSES: int = 6
RANK: int = 8

BF16: int = 2            # bytes for one weight stored as bfloat16
TRAINED_BYTES: int = 12  # weight 2 + gradient 2 + two float32 optimiser averages
SAVED_PER_TOKEN: int = 10   # stated: numbers kept per token per block for the backward pass

DESKTOP: float = 40e12   # stated: operations a second an ordinary desktop card sustains
RENTED: float = 160e12   # stated: the example accelerator of the scale page
RENT_PER_HOUR: float = 2.0   # stated: dollars an accelerator-hour

BIG_N: int = 6_738_415_616   # the stated 7 thousand million parameter model
BIG_TOKENS: int = 400        # tokens in one example of the language job


class Shape:
    """Parameter counts for the stated picture model, worked out from the shape."""

    def __init__(self) -> None:
        self.patch_embed = 3 * PATCH * PATCH * WIDTH + WIDTH
        self.positions = TOKENS * WIDTH + WIDTH          # position table plus summary token
        self.attn = 4 * WIDTH * WIDTH + 4 * WIDTH
        self.ff = 2 * WIDTH * FF + FF + WIDTH
        self.norms = 4 * WIDTH
        self.block = self.attn + self.ff + self.norms
        self.backbone = (self.patch_embed + self.positions
                         + BLOCKS * self.block + 2 * WIDTH)
        self.head = WIDTH * JOB_CLASSES + JOB_CLASSES
        self.whole = self.backbone + self.head
        # adapters, at rank RANK
        self.lora_qv = BLOCKS * 2 * (2 * RANK * WIDTH)
        self.lora_out_ff = BLOCKS * (2 * RANK * WIDTH + 2 * RANK * (WIDTH + FF))
        # one forward pass over one picture, in floating-point operations
        self.fwd_matmul = 2 * self.backbone * TOKENS
        self.fwd_scores = 4 * TOKENS * TOKENS * WIDTH * BLOCKS
        self.fwd = self.fwd_matmul + self.fwd_scores
        self.scores_share = self.fwd_scores / self.fwd_matmul

    def report(self) -> None:
        print('--- the stated picture model ---')
        print(f'the stated shape            {IMG} by {IMG} pixels, {PATCH} by {PATCH} '
              f'patches, {BLOCKS} blocks, width {WIDTH}, feed-forward inner width {FF}')
        print(f'tokens per picture          {TOKENS}')
        print(f'patch embedding             {self.patch_embed:,}')
        print(f'position table + token      {self.positions:,}')
        print(f'attention, one block        {self.attn:,}')
        print(f'feed-forward, one block     {self.ff:,}')
        print(f'one block                   {self.block:,}')
        print(f'{BLOCKS} blocks                   {BLOCKS * self.block:,}')
        print(f'backbone                    {self.backbone:,}')
        print(f'a {JOB_CLASSES}-way head                {self.head:,}')
        print(f'backbone + head             {self.whole:,}')
        print(f'rank-{RANK} adapter, query+value {self.lora_qv:,} '
              f'({100 * self.lora_qv / self.backbone:.3f}% of the backbone)')
        print(f'rank-{RANK} adapter, out+ff      {self.lora_out_ff:,} '
              f'({100 * self.lora_out_ff / self.backbone:.3f}% of the backbone)')
        print(f'forward, matrix multiplies  {self.fwd_matmul:.4g} FLOP a picture')
        print(f'forward, attention scores   {self.fwd_scores:.4g} FLOP a picture '
              f'({100 * self.scores_share:.1f}% more)')


SH = Shape()


# the six rungs, in order, with what each one lets training change
RUNG_NAMES: list[str] = ['use it as it is', 'a better prompt', 'a head on frozen features',
                         'an adapter', 'a full fine-tune', 'train from nothing']
RUNG_SHORT: list[str] = ['as it is', 'prompt', 'head', 'adapter', 'full', 'scratch']


def rung_trainable() -> list[int]:
    """How many numbers each rung changes, for the stated picture model."""
    return [0, 0, SH.head, SH.lora_out_ff + SH.head, SH.whole, SH.whole]


def rung_kept_bytes() -> list[float]:
    """Bytes you must keep for each extra job you adapt the model for."""
    prompt_text = 400 * 4          # 400 tokens of prompt, 4 bytes a token of text
    return [0.0, float(prompt_text), SH.head * BF16,
            (SH.lora_out_ff + SH.head) * BF16, SH.whole * BF16, SH.whole * BF16]


class Run:
    """A stated training run: 500 pictures, 30 passes over them, batches of 32."""

    pictures: int = 500
    passes: int = 30
    batch: int = 32

    def __init__(self) -> None:
        self.steps_pictures = self.pictures * self.passes
        # arithmetic per picture per pass, by rung
        self.flop_per_picture = [
            0.0,                                  # as it is: no training at all
            0.0,                                  # a prompt: no training at all
            0.0,                                  # the head trains on cached features
            4.0 * SH.backbone * TOKENS,           # adapter: forward plus one backward
            6.0 * SH.whole * TOKENS,              # full: forward plus both backwards
            6.0 * SH.whole * TOKENS,              # from nothing: the same per pass
        ]
        self.cache_flop = self.pictures * SH.fwd   # one forward pass a picture, once
        head_flop = 2.0 * 3 * SH.head * self.pictures * 200   # 200 passes over cached features
        self.flop = []
        for i, per in enumerate(self.flop_per_picture):
            total = per * self.steps_pictures
            if i == 2:
                total = self.cache_flop + head_flop
            if i in (0, 1):
                total = 0.0
            self.flop.append(total)
        self.head_flop = head_flop
        # memory, in bytes, at batch 32
        act = SAVED_PER_TOKEN * TOKENS * WIDTH * BLOCKS * BF16 * self.batch
        self.activations = [0.0, 0.0, 0.0, float(act), float(act), float(act)]
        self.frozen = [SH.whole * BF16, SH.whole * BF16, SH.backbone * BF16,
                       SH.backbone * BF16, 0.0, 0.0]
        self.trained = [0.0, 0.0, SH.head * TRAINED_BYTES,
                        (SH.lora_out_ff + SH.head) * TRAINED_BYTES,
                        SH.whole * TRAINED_BYTES, SH.whole * TRAINED_BYTES]
        self.memory = [self.frozen[i] + self.trained[i] + self.activations[i]
                       for i in range(6)]
        # the same recipe on the stated big model, for contrast
        big_lora = 4_194_304
        self.big_memory_full = BIG_N * TRAINED_BYTES
        self.big_memory_lora = BIG_N * BF16 + big_lora * TRAINED_BYTES
        self.big_lora = big_lora

    def report(self) -> None:
        print(f'--- a stated run: {self.pictures} pictures, {self.passes} passes, '
              f'batches of {self.batch} ---')
        for i, name in enumerate(RUNG_NAMES):
            secs = self.flop[i] / DESKTOP
            print(f'{name:28s} {self.flop[i]:10.4g} FLOP  '
                  f'{secs:8.1f} s on the desktop card  '
                  f'{self.memory[i] / 2 ** 30:6.2f} GiB')
        print(f'caching the features costs  {self.cache_flop:.4g} FLOP '
              f'({self.cache_flop / DESKTOP:.1f} s), the head itself '
              f'{self.head_flop:.4g} FLOP')
        print(f'activations at batch {self.batch}     '
              f'{self.activations[4] / 2 ** 30:.2f} GiB')
        print(f'the big model, full fine-tune {self.big_memory_full / 2 ** 30:.2f} GiB, '
              f'with a rank-8 adapter {self.big_memory_lora / 2 ** 30:.2f} GiB')


RUN = Run()


# --- human time, at stated rates -----------------------------------------

PICTURES_AN_HOUR: float = 200.0      # stated: taking and labelling one picture of a tray
DEMOS_AN_HOUR: float = 40.0          # stated: one demonstration, including resetting the scene
PROBE_HOURS: float = 20.0 / 60.0     # stated: a person's time for one frozen-feature probe
ATTEMPT_HOURS: float = 6.0           # stated: a person's time for one fine-tuning attempt


class Pretrain:
    """What training a model of each size from nothing costs."""

    def __init__(self) -> None:
        self.small_pictures = 1_200_000
        self.small_passes = 300
        self.small_flop = (6.0 * SH.backbone * TOKENS
                           * self.small_pictures * self.small_passes)
        self.big_tokens = 1.4e12
        self.big_flop = 6.0 * BIG_N * self.big_tokens
        self.huge_n = 70e9
        self.huge_tokens = 10e12
        self.huge_flop = 6.0 * self.huge_n * self.huge_tokens
        self.names = ['the 85.8 million\npicture backbone',
                      'the 6.74 thousand million\nlanguage model',
                      'a 70 thousand million\nlanguage model']
        self.flops = [self.small_flop, self.big_flop, self.huge_flop]
        # a small model that is genuinely reachable
        self.tiny_n = 1_000_000
        self.tiny_examples = 5_000
        self.tiny_passes = 200
        self.tiny_flop = (6.0 * self.tiny_n * self.tiny_examples * self.tiny_passes)
        # the human cost of the data, at the stated rates
        self.working_year = 1800.0                  # stated: hours a person works in a year
        self.small_hours = self.small_pictures / PICTURES_AN_HOUR
        self.small_years = self.small_hours / self.working_year
        self.year_pictures = self.working_year * PICTURES_AN_HOUR
        self.year_demos = self.working_year * DEMOS_AN_HOUR
        self.year_frames = self.year_demos * 500
        self.year_share = self.year_pictures / self.small_pictures

    def days(self, flop: float, rate: float, cards: int) -> float:
        return flop / (rate * cards) / 86400.0

    def report(self) -> None:
        print('--- training from nothing ---')
        for name, flop in zip(self.names, self.flops):
            line = name.replace('\n', ' ')
            print(f'{line:44s} {flop:9.3g} FLOP  '
                  f'{self.days(flop, DESKTOP, 1):10.1f} days on 1 desktop card  '
                  f'{self.days(flop, RENTED, 1):9.1f} on 1 rented  '
                  f'{self.days(flop, RENTED, 512):7.2f} on 512')
        print(f'the backbone pretrain, in years on one desktop card '
              f'{self.days(self.small_flop, DESKTOP, 1) / 365.25:.2f}')
        print(f'the big pretrain, in years on one desktop card    '
              f'{self.days(self.big_flop, DESKTOP, 1) / 365.25:.1f}')
        print(f'the big pretrain, rented at ${RENT_PER_HOUR:.0f} an accelerator-hour '
              f'${self.big_flop / RENTED / 3600 * RENT_PER_HOUR:,.0f}')
        print(f'a 1 million parameter model on {self.tiny_examples} examples: '
              f'{self.tiny_flop:.3g} FLOP, '
              f'{self.tiny_flop / DESKTOP:.1f} s on the desktop card')
        print(f'{self.small_pictures:,} pictures at {PICTURES_AN_HOUR:.0f} an hour '
              f'= {self.small_hours:,.0f} hours = '
              f'{self.small_years:.1f} working years')
        print(f'one person working {self.working_year:,.0f} hours collects '
              f'{self.year_pictures:,.0f} pictures, which is '
              f'{100 * self.year_share:.0f}% of that set, or '
              f'{self.year_demos:,.0f} demonstrations, which is '
              f'{self.year_frames:,.0f} frames of the same few scenes')
        print(f'your {RUN.pictures} pictures are '
              f'{100 * RUN.pictures / self.small_pictures:.3f}% of the pretraining set, '
              f'which is {self.small_pictures / RUN.pictures:,.0f} times smaller')


PRE = Pretrain()


def budget_report() -> dict[str, float]:
    """One stated budget of 200 accelerator-hours, spent three ways."""
    budget_flop = 200 * 3600 * RENTED
    out = {
        'budget_flop': budget_flop,
        'share_of_pretrain': 100 * budget_flop / PRE.big_flop,
        'full_runs': budget_flop / RUN.flop[4],
        'adapter_runs': budget_flop / RUN.flop[3],
        'probe_runs': budget_flop / RUN.flop[2],
    }
    print('--- one stated budget of 200 accelerator-hours ---')
    print(f'{budget_flop:.3g} FLOP, which is '
          f'{out["share_of_pretrain"]:.4f}% of the big pretrain, or '
          f'{out["full_runs"]:,.0f} full fine-tunes, or '
          f'{out["adapter_runs"]:,.0f} adapter runs, or '
          f'{out["probe_runs"]:,.0f} frozen-feature probes '
          f'of the stated picture model')
    return out

# ==========================================================================
# PART TWO: the simulated world, and the ladder measured in it
# ==========================================================================
#
# One example is 200 numbers, standing in for one look at one object. Behind
# those numbers are 16 hidden ones: 6 "part strengths", which say how strongly
# each of six features of the object is present, and 10 nuisance numbers,
# which stand for the lighting, the background and the pose and have nothing
# to do with any job. The 200 numbers are a fixed random mixture of all 16,
# put through a cosine, so reading a part strength back out of them is
# possible but not easy, which is the point: it is the thing pretraining pays
# for. The source job the published model was trained on is to say which part
# is strongest. The new job is a different question about the same parts: it
# asks whether parts one and two are both present, exactly one of them, or
# neither, which is a question no sum of the part strengths can answer.

PARTS: int = 6
NUISANCE: int = 10
LATENT: int = PARTS + NUISANCE
OBS: int = 200
H1: int = 48
H2: int = 24
TGT_CLASSES: int = 3
MIX_SCALE: float = 0.30      # spread of the fixed random mixing weights
LOOK_NOISE: float = 0.30     # how noisily one look reports a part strength
NUISANCE_SPREAD: float = 1.0

SIZES: list[int] = [4, 8, 16, 32, 64, 128, 256, 512, 1024]
SEEDS: int = 10
PRETRAIN_EXAMPLES: int = 12000
PRETRAIN_STEPS: int = 2500
PRETRAIN_BATCH: int = 256

# the learning rate and the number of steps for each rung, each chosen once
RUNG_FIT: dict[str, tuple[int, float]] = {
    'head': (300, 0.30), 'adapter': (300, 0.08),
    'full': (600, 0.05), 'scratch': (600, 0.08),
}
ADAPTER_RANK: int = 2


class World:
    """One simulated world: the mixing, the source job and the new job."""

    def __init__(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)
        self.mix = self.rng.normal(0.0, MIX_SCALE, size=(LATENT, OBS))
        self.phase = self.rng.uniform(0.0, 2.0 * np.pi, size=OBS)

    def draw(self, n: int, job: str) -> tuple[Arr, Ints, Arr]:
        rng = self.rng
        parts = rng.normal(0.0, 1.0, size=(n, PARTS))
        if job == 'source':
            y = parts.argmax(axis=1)
        else:
            first = parts[:, 0] > 0.0
            second = parts[:, 1] > 0.0
            y = np.where(first & second, 0, np.where(first ^ second, 1, 2))
        seen = np.concatenate(
            [parts + rng.normal(0.0, LOOK_NOISE, size=(n, PARTS)),
             rng.normal(0.0, NUISANCE_SPREAD, size=(n, NUISANCE))], axis=1)
        x = np.cos(seen @ self.mix + self.phase) + rng.normal(0.0, 0.02, size=(n, OBS))
        return x, y.astype(np.int64), seen

    def ceiling(self, seen: Arr, y: Ints) -> float:
        """The best accuracy anything could reach, reading the noisy parts."""
        first = seen[:, 0] > 0.0
        second = seen[:, 1] > 0.0
        best = np.where(first & second, 0, np.where(first ^ second, 1, 2))
        return float((best == y).mean())


def _init_net(rng: np.random.Generator, n_in: int, out: int) -> list[Arr]:
    def w(a: int, b: int) -> Arr:
        return rng.normal(0.0, np.sqrt(2.0 / a), size=(a, b))
    return [w(n_in, H1), np.zeros(H1), w(H1, H2), np.zeros(H2), w(H2, out), np.zeros(out)]


def _forward(p: list[Arr], x: Arr) -> tuple[Arr, Arr, Arr]:
    h1 = np.maximum(0.0, x @ p[0] + p[1])
    h2 = np.maximum(0.0, h1 @ p[2] + p[3])
    return h1, h2, h2 @ p[4] + p[5]


def _with_adapter(p: list[Arr], extra: dict[str, Arr]) -> list[Arr]:
    out = list(p)
    for j, idx in enumerate((0, 2)):
        out[idx] = p[idx] + extra[f'a{j}'] @ extra[f'b{j}']
    return out


CLIP: float = 5.0        # the largest gradient length any step is allowed to use


def _train(p: list[Arr], x: Arr, y: Ints, steps: int, lr: float, free: list[int],
           extra: dict[str, Arr] | None = None, batch: int = 0,
           rng: np.random.Generator | None = None) -> list[Arr]:
    """Momentum gradient descent on the free weights, and on the adapter if given.

    The gradient is shortened to CLIP whenever it is longer than that, which is
    what keeps the larger learning rates here from blowing up. With `batch` set,
    each step uses a fresh random handful of the examples rather than all of them.
    """
    p = [q.copy() for q in p]
    vel = [np.zeros_like(q) for q in p]
    evel = {k: np.zeros_like(v) for k, v in (extra or {}).items()}
    for _ in range(steps):
        if batch and rng is not None:
            take = rng.integers(0, len(x), size=batch)
            xb, yb = x[take], y[take]
        else:
            xb, yb = x, y
        n = len(xb)
        base = _with_adapter(p, extra) if extra is not None else p
        h1, h2, z = _forward(base, xb)
        dz = _softmax(z)
        dz[np.arange(n), yb] -= 1.0
        dz /= n
        g: list[Arr] = [np.zeros(0)] * 6
        g[4] = h2.T @ dz
        g[5] = dz.sum(axis=0)
        dh2 = (dz @ base[4].T) * (h2 > 0)
        g[2] = h1.T @ dh2
        g[3] = dh2.sum(axis=0)
        dh1 = (dh2 @ base[2].T) * (h1 > 0)
        g[0] = xb.T @ dh1
        g[1] = dh1.sum(axis=0)
        length = np.sqrt(sum(float((q * q).sum()) for q in g))
        step = lr * min(1.0, CLIP / (length + 1e-12))
        if extra is not None:
            for j, idx in enumerate((0, 2)):
                pairs = (('a', g[idx] @ extra[f'b{j}'].T),
                         ('b', extra[f'a{j}'].T @ g[idx]))
                for key, grad in pairs:
                    k = f'{key}{j}'
                    evel[k] = 0.9 * evel[k] - step * grad
                    extra[k] = extra[k] + evel[k]
        for i in free:
            vel[i] = 0.9 * vel[i] - step * g[i]
            p[i] = p[i] + vel[i]
    return p


def _acc(p: list[Arr], x: Arr, y: Ints, extra: dict[str, Arr] | None = None) -> float:
    base = _with_adapter(p, extra) if extra is not None else p
    return float((_forward(base, x)[2].argmax(axis=1) == y).mean())


def _new_head(rng: np.random.Generator, net: list[Arr], out: int) -> list[Arr]:
    return net[:4] + [rng.normal(0.0, 0.1, size=(H2, out)), np.zeros(out)]


def _adapter(rng: np.random.Generator, rank: int) -> dict[str, Arr]:
    return {'a0': rng.normal(0.0, 0.05, size=(OBS, rank)), 'b0': np.zeros((rank, H1)),
            'a1': rng.normal(0.0, 0.05, size=(H1, rank)), 'b1': np.zeros((rank, H2))}


class Ladder:
    """The six rungs measured in the simulated world, averaged over SEEDS runs."""

    def __init__(self) -> None:
        self.test = np.zeros((6, len(SIZES)))
        self.train = np.zeros((6, len(SIZES)))
        ceil, src = [], []
        for seed in range(SEEDS):
            te, tr, c, s = self._one(100 + seed)
            self.test += te / SEEDS
            self.train += tr / SEEDS
            ceil.append(c)
            src.append(s)
        self.ceiling = float(np.mean(ceil))
        self.source_acc = float(np.mean(src))
        self.need = [self._examples_to_match(i) for i in range(6)]

    def _one(self, seed: int) -> tuple[Arr, Arr, float, float]:
        world = World(seed)
        rng = world.rng
        xs, ys, _ = world.draw(PRETRAIN_EXAMPLES, 'source')
        xs_t, ys_t, _ = world.draw(1500, 'source')
        net = _train(_init_net(rng, OBS, PARTS), xs, ys, PRETRAIN_STEPS, 0.08,
                     [0, 1, 2, 3, 4, 5], batch=PRETRAIN_BATCH, rng=rng)
        source_acc = _acc(net, xs_t, ys_t)
        x_te, y_te, seen_te = world.draw(1500, 'new')
        ceiling = world.ceiling(seen_te, y_te)

        test = np.zeros((6, len(SIZES)))
        train = np.zeros((6, len(SIZES)))
        _, _, z_te = _forward(net, x_te)
        said_te = z_te.argmax(axis=1)
        for k, n in enumerate(SIZES):
            xt, yt, _ = world.draw(n, 'new')
            _, _, z_tr = _forward(net, xt)
            said_tr = z_tr.argmax(axis=1)

            # rung 1: use it as it is, reading its class k as your label k
            test[0, k] = float((said_te % TGT_CLASSES == y_te).mean())
            train[0, k] = float((said_tr % TGT_CLASSES == yt).mean())

            # rung 2: a prompt, which chooses the best fixed reading of its
            # existing classes from the few examples you have, and trains nothing
            pick = min(n, 24)
            table = np.zeros(PARTS, dtype=np.int64)
            for c in range(PARTS):
                m = said_tr[:pick] == c
                table[c] = (np.bincount(yt[:pick][m], minlength=TGT_CLASSES).argmax()
                            if m.any() else 0)
            test[1, k] = float((table[said_te] == y_te).mean())
            train[1, k] = float((table[said_tr] == yt).mean())

            # rung 3: a new head on the frozen features
            steps, lr = RUNG_FIT['head']
            head = _train(_new_head(rng, net, TGT_CLASSES), xt, yt, steps, lr, [4, 5])
            train[2, k] = _acc(head, xt, yt)
            test[2, k] = _acc(head, x_te, y_te)

            # rung 4: a rank-2 adapter beside both hidden weight matrices
            steps, lr = RUNG_FIT['adapter']
            extra = _adapter(rng, ADAPTER_RANK)
            ad = _train(_new_head(rng, net, TGT_CLASSES), xt, yt, steps, lr, [4, 5], extra)
            train[3, k] = _acc(ad, xt, yt, extra)
            test[3, k] = _acc(ad, x_te, y_te, extra)

            # rung 5: a full fine-tune
            steps, lr = RUNG_FIT['full']
            fu = _train(_new_head(rng, net, TGT_CLASSES), xt, yt, steps, lr,
                        [0, 1, 2, 3, 4, 5])
            train[4, k] = _acc(fu, xt, yt)
            test[4, k] = _acc(fu, x_te, y_te)

            # rung 6: the same shape, from a random start, on your examples only
            steps, lr = RUNG_FIT['scratch']
            sc = _train(_init_net(rng, OBS, TGT_CLASSES), xt, yt, steps, lr,
                        [0, 1, 2, 3, 4, 5])
            train[5, k] = _acc(sc, xt, yt)
            test[5, k] = _acc(sc, x_te, y_te)
        return test, train, ceiling, source_acc

    def _examples_to_match(self, rung: int) -> float:
        """How many examples this rung needs to reach what a fine-tune reaches at 64."""
        target = self.test[4, SIZES.index(64)]
        row = self.test[rung]
        for k in range(len(SIZES)):
            if row[k] >= target:
                if k == 0:
                    return float(SIZES[0])
                lo, hi = SIZES[k - 1], SIZES[k]
                span = row[k] - row[k - 1]
                if span <= 0:
                    return float(hi)
                frac = (target - row[k - 1]) / span
                return float(lo + frac * (hi - lo))
        return float('inf')

    def report(self) -> None:
        print(f'--- the simulated ladder, {SEEDS} worlds, held-out accuracy ---')
        print(f'the published model scores {self.source_acc:.3f} on its own '
              f'{PARTS}-way job; the best anything could do on the new job is '
              f'{self.ceiling:.3f}; guessing scores {1 / TGT_CLASSES:.3f}')
        print(f'{"":27s}' + '  '.join(f'{n:>5d}' for n in SIZES))
        for i, name in enumerate(RUNG_NAMES):
            print(f'{name:27s}' + '  '.join(f'{v:5.3f}' for v in self.test[i]))
        print('--- the same runs, accuracy on the examples it trained on ---')
        for i, name in enumerate(RUNG_NAMES):
            print(f'{name:27s}' + '  '.join(f'{v:5.3f}' for v in self.train[i]))
        k64, k512 = SIZES.index(64), SIZES.index(512)
        print(f'at 64 examples: head {self.test[2, k64]:.3f}, adapter '
              f'{self.test[3, k64]:.3f}, full {self.test[4, k64]:.3f}, '
              f'from nothing {self.test[5, k64]:.3f}')
        print(f'at 512 examples: head {self.test[2, k512]:.3f}, adapter '
              f'{self.test[3, k512]:.3f}, full {self.test[4, k512]:.3f}, '
              f'from nothing {self.test[5, k512]:.3f}')
        print(f'the head fits {self.train[2, k64]:.3f} of its own 64 examples and '
              f'reaches {self.test[2, k64]:.3f} held out; the full fine-tune fits '
              f'{self.train[4, k64]:.3f} and reaches {self.test[4, k64]:.3f}; '
              f'from nothing fits {self.train[5, k64]:.3f} and reaches '
              f'{self.test[5, k64]:.3f}')
        print(f'a full fine-tune on 64 examples reaches '
              f'{self.test[4, k64]:.3f}; to reach that, each rung needs:')
        for i, name in enumerate(RUNG_NAMES):
            v = self.need[i]
            print(f'  {name:27s} {"more than 1024" if v == float("inf") else f"{v:.0f}"}'
                  f' examples')
        gain = [self.test[i, k512] - self.test[i - 1, k512] for i in range(1, 6)]
        print('the gain from climbing one rung, at 512 examples: '
              + ', '.join(f'{RUNG_SHORT[i + 1]} {g:+.3f}' for i, g in enumerate(gain)))


# ==========================================================================
# PART THREE: choosing between published starting points
# ==========================================================================

CANDIDATES: int = 8


class Candidates:
    """Eight simulated published models, scored on their own job and on ours.

    Each is pretrained on its own source job, which asks which of four
    directions in part space is strongest. A candidate's directions lie partly
    in the two parts our job depends on and partly in the four it does not,
    and that share is the only thing set on purpose. How hard its own job is,
    and so how well it scores on it, is drawn separately, so nothing ties a
    candidate's own score to what it is worth to us.
    """

    def __init__(self) -> None:
        rng = np.random.default_rng(11)
        self.share = np.linspace(0.05, 0.95, CANDIDATES)
        # how many classes each candidate's own job has, which sets the score it
        # publishes without changing what its features are worth to us
        self.own_classes = rng.permutation(np.array([3, 3, 4, 4, 6, 6, 8, 8]))
        self.own: list[float] = []
        self.overlap: list[float] = []
        self.probe: list[float] = []
        self.ft: list[float] = []
        self.ceiling = 0.0
        for i in range(CANDIDATES):
            o, ov, pr, ft, ceil = self._one(i, rng)
            self.own.append(o)
            self.overlap.append(ov)
            self.probe.append(pr)
            self.ft.append(ft)
            self.ceiling = ceil
        self.own_a = np.array(self.own)
        self.overlap_a = np.array(self.overlap)
        self.probe_a = np.array(self.probe)
        self.ft_a = np.array(self.ft)
        self.r_own = float(stats.pearsonr(self.own_a, self.ft_a).statistic)
        self.r_overlap = float(stats.pearsonr(self.overlap_a, self.ft_a).statistic)
        self.rho_probe = float(stats.spearmanr(self.probe_a, self.ft_a).statistic)
        self.best_ft = int(self.ft_a.argmax())
        self.best_probe = int(self.probe_a.argmax())
        self.best_own = int(self.own_a.argmax())
        self.gap_own = float(self.ft_a[self.best_ft] - self.ft_a[self.best_own])
        self.gap_probe = float(self.ft_a[self.best_ft] - self.ft_a[self.best_probe])
        self.probe_hours = CANDIDATES * PROBE_HOURS
        self.attempt_hours = CANDIDATES * ATTEMPT_HOURS
        self.saved_hours = self.attempt_hours - self.probe_hours

    def _one(self, i: int, rng: np.random.Generator) -> tuple[float, float, float, float, float]:
        world = World(500 + i)
        share = self.share[i]
        classes = int(self.own_classes[i])
        near_mask = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0])
        dirs = []
        for _ in range(classes):
            raw = rng.normal(0.0, 1.0, size=PARTS)
            near = raw * near_mask
            far = raw * (1.0 - near_mask)
            d = (share * near / (np.linalg.norm(near) + 1e-9)
                 + (1 - share) * far / (np.linalg.norm(far) + 1e-9))
            dirs.append(d / (np.linalg.norm(d) + 1e-9))
        basis = np.array(dirs)

        def source(n: int) -> tuple[Arr, Ints]:
            parts = world.rng.normal(0.0, 1.0, size=(n, PARTS))
            y = (parts @ basis.T).argmax(axis=1)
            seen = np.concatenate(
                [parts + world.rng.normal(0.0, LOOK_NOISE, size=(n, PARTS)),
                 world.rng.normal(0.0, NUISANCE_SPREAD, size=(n, NUISANCE))], axis=1)
            x = np.cos(seen @ world.mix + world.phase) + world.rng.normal(
                0.0, 0.02, size=(n, OBS))
            return x, y.astype(np.int64)

        xs, ys = source(PRETRAIN_EXAMPLES)
        xs_t, ys_t = source(1500)
        net = _train(_init_net(rng, OBS, classes), xs, ys, PRETRAIN_STEPS, 0.08,
                     [0, 1, 2, 3, 4, 5], batch=PRETRAIN_BATCH, rng=rng)
        own = _acc(net, xs_t, ys_t)

        # the overlap, measured rather than assumed: how well a straight line
        # through the frozen features recovers the two parts our job needs
        x_fit, _, seen_fit = world.draw(600, 'new')
        _, feat_fit, _ = _forward(net, x_fit)
        a = np.concatenate([feat_fit, np.ones((len(feat_fit), 1))], axis=1)
        coef, *_ = np.linalg.lstsq(a, seen_fit[:, :2], rcond=None)
        pred = a @ coef
        resid = ((pred - seen_fit[:, :2]) ** 2).sum()
        spread = ((seen_fit[:, :2] - seen_fit[:, :2].mean(axis=0)) ** 2).sum()
        overlap = float(1.0 - resid / spread)

        x_probe, y_probe, _ = world.draw(64, 'new')
        x_tr, y_tr, _ = world.draw(512, 'new')
        x_te, y_te, seen_te = world.draw(1500, 'new')
        steps, lr = RUNG_FIT['head']
        pr = _train(_new_head(rng, net, TGT_CLASSES), x_probe, y_probe, steps, lr, [4, 5])
        steps, lr = RUNG_FIT['full']
        fu = _train(_new_head(rng, net, TGT_CLASSES), x_tr, y_tr, steps, lr,
                    [0, 1, 2, 3, 4, 5])
        return (own, overlap, _acc(pr, x_te, y_te), _acc(fu, x_te, y_te),
                world.ceiling(seen_te, y_te))

    def report(self) -> None:
        print(f'--- {CANDIDATES} simulated published models, one new job ---')
        print(f'the best anything could do on the new job is {self.ceiling:.3f}')
        print(f'{"model":>6s} {"classes":>8s} {"own job":>8s} {"overlap":>8s} '
              f'{"probe 64":>9s} {"tune 512":>9s}')
        for i in range(CANDIDATES):
            print(f'{chr(65 + i):>6s} {self.own_classes[i]:8d} {self.own[i]:8.4f} '
                  f'{self.overlap[i]:8.4f} {self.probe[i]:9.4f} {self.ft[i]:9.4f}')
        by_probe = ''.join(chr(65 + i) for i in np.argsort(self.probe_a))
        by_ft = ''.join(chr(65 + i) for i in np.argsort(self.ft_a))
        print(f'the probe ranks them     {by_probe}')
        print(f'the fine-tune ranks them {by_ft}')
        print(f'its score on its own job against its worth here: r = {self.r_own:+.3f}')
        print(f'its overlap with our job against its worth here: r = '
              f'{self.r_overlap:+.3f}')
        print(f'the 64-example probe against the 512-example fine-tune: '
              f'rank correlation {self.rho_probe:+.3f}')
        print(f'the best model here is {chr(65 + self.best_ft)} at '
              f'{self.ft[self.best_ft]:.3f}; picking by its own score gives '
              f'{chr(65 + self.best_own)}, which ends {self.gap_own:.3f} lower; '
              f'picking by the probe gives {chr(65 + self.best_probe)}, which ends '
              f'{self.gap_probe:.3f} lower')
        print(f'screening {CANDIDATES} candidates with a probe costs '
              f'{self.probe_hours:.1f} hours of a person at the stated rates, and '
              f'fine-tuning all {CANDIDATES} costs {self.attempt_hours:.0f} hours, '
              f'so the probe saves {self.saved_hours:.1f} hours')


# ==========================================================================
# PART FOUR: licences and the three worked jobs
# ==========================================================================

TERMS: list[tuple[str, str]] = [
    ('the code', 'the training and serving programs'),
    ('the weights', 'the file of numbers you download'),
    ('the use', 'an acceptable-use policy naming uses that are not allowed'),
    ('the pretraining data', 'the pictures, text and video the weights were made from'),
    ('your own data', 'what your customer or your employer let you record'),
]

CLAUSES: list[str] = ['research only,\nno commercial use',
                      'no use above a\nstated size of company',
                      'outputs may not train\nanother model',
                      'named uses are\nforbidden outright',
                      'derivatives must carry\nthe same terms']
USES: list[str] = ['a demonstration\nin the lab', 'a tool your\ncompany uses',
                   'a product you\nsell', 'weights you\npass on']
# 1 means the clause kind blocks that use, 0 means it does not; stated examples
BLOCKS_GRID: list[list[int]] = [
    [0, 1, 1, 1],
    [0, 1, 1, 0],
    [0, 0, 1, 1],
    [1, 1, 1, 1],
    [0, 0, 0, 1],
]

STAGES: list[tuple[str, float]] = [
    ('choose a starting point', 0.3),
    ('collect 500 pictures', RUN.pictures / PICTURES_AN_HOUR),
    ('check and fix the labels', 1.5),
    ('write the training code', 6.0),
    ('run and tune it', 8.0),
    ('judge it on the arm', 6.0),
    ('put it in the cell', 12.0),
]
READ_TERMS_HOURS: float = 0.5


def licence_report() -> dict[str, float]:
    total = sum(h for _, h in STAGES)
    blocked = sum(sum(row) for row in BLOCKS_GRID)
    print('--- licences ---')
    print(f'{len(TERMS)} separate sets of terms touch one deployed model')
    print(f'of the {len(CLAUSES)} x {len(USES)} = {len(CLAUSES) * len(USES)} cells in the '
          f'stated clause grid, {blocked} are blocked')
    for i, row in enumerate(BLOCKS_GRID):
        print(f'  {CLAUSES[i]!r:46s} blocks {sum(row)} of {len(USES)} uses')
    for j, use in enumerate(USES):
        n = sum(row[j] for row in BLOCKS_GRID)
        print(f'  {use.replace(chr(10), " ")!r:30s} is blocked by {n} of '
              f'{len(CLAUSES)} clause kinds')
    print(f'the work the terms protect is {total:.1f} hours; reading them costs '
          f'{READ_TERMS_HOURS:.1f} hours, which is {total / READ_TERMS_HOURS:.0f} '
          f'times less')
    return {'total_hours': total, 'blocked': float(blocked)}


class Jobs:
    """Three concrete robot jobs, taken down the ladder."""

    def __init__(self) -> None:
        # job A: tell six part types apart on a tray, fixed overhead camera
        self.a_factors = [('part types', 6), ('ways of lying', 8),
                          ('lighting conditions', 3), ('places on the tray', 4)]
        self.a_combinations = 1
        for _, v in self.a_factors:
            self.a_combinations *= v
        self.a_full = self.a_combinations * 2
        self.a_hours = self.a_full / PICTURES_AN_HOUR
        # job B: turn a spoken instruction into one of 20 task calls
        self.b_calls = 20
        self.b_examples_if_trained = self.b_calls * 30
        self.b_prompt_tokens = 450
        self.b_calls_a_day = 400
        self.b_prompt_flop_a_day = (2.0 * BIG_N * self.b_prompt_tokens
                                    * self.b_calls_a_day)
        self.b_tune_flop = (6.0 * BIG_N * BIG_TOKENS * self.b_examples_if_trained * 3)
        self.b_crossover = self.b_tune_flop / (2.0 * BIG_N * self.b_prompt_tokens)
        self.b_days = self.b_crossover / self.b_calls_a_day
        # job C: pick up one soft part with your own gripper
        self.c_factors = [('starting places', 5), ('ways the part lies', 4),
                          ('heights of the stack', 3)]
        self.c_combinations = 1
        for _, v in self.c_factors:
            self.c_combinations *= v
        self.c_demos = self.c_combinations * 2
        self.c_hours = self.c_demos / DEMOS_AN_HOUR
        self.c_frames = self.c_demos * 500
        self.c_scenes = self.c_combinations
        self.c_scratch_hours = PRE.small_hours
        self.c_scratch_years = PRE.small_years

    def report(self) -> None:
        print('--- three jobs ---')
        print(f'job A: {" x ".join(str(v) for _, v in self.a_factors)} = '
              f'{self.a_combinations} combinations, two pictures each = '
              f'{self.a_full} pictures = {self.a_hours:.1f} hours at '
              f'{PICTURES_AN_HOUR:.0f} an hour')
        print(f'job B: {self.b_calls} calls would need about '
              f'{self.b_examples_if_trained} written examples to fine-tune; a '
              f'{self.b_prompt_tokens}-token prompt costs '
              f'{self.b_prompt_flop_a_day:.3g} FLOP a day at '
              f'{self.b_calls_a_day} calls, and matches the fine-tune '
              f'({self.b_tune_flop:.3g} FLOP) after {self.b_crossover:,.0f} calls, '
              f'which is {self.b_days:.0f} days')
        print(f'job C: {" x ".join(str(v) for _, v in self.c_factors)} = '
              f'{self.c_combinations} combinations, two demonstrations each = '
              f'{self.c_demos} demonstrations = {self.c_hours:.1f} hours at '
              f'{DEMOS_AN_HOUR:.0f} an hour, giving {self.c_frames:,} frames')
        print(f'job C gives {self.c_scenes} distinct scenes; the seeing part of a '
              f'published model came from {PRE.small_pictures:,} different scenes, '
              f'which at {PICTURES_AN_HOUR:.0f} an hour is '
              f'{self.c_scratch_hours:,.0f} hours, or '
              f'{self.c_scratch_years:.1f} working years, and that is '
              f'{self.c_scratch_hours / self.c_hours:,.0f} times job C\'s '
              f'{self.c_hours:.0f} hours of collecting')

# ==========================================================================
# PART FIVE: the pictures
# ==========================================================================

RUNG_COLOURS: list[str] = [MUTED, '#8ab4d8', LINK, TEAL, PURPLE, GRIP]


def fig_ladder_what_moves() -> None:
    """Six copies of the stated model, coloured by what each rung lets training change."""
    fig, axes = plt.subplots(1, 6, figsize=(13.6, 4.5))
    counts = rung_trainable()
    for r, ax in enumerate(axes):
        _blank(ax)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.1, 1.08)
        hatch = '///' if r == 5 else None
        for b in range(BLOCKS):
            y = 0.06 + b * 0.072
            face = RUNG_COLOURS[r] if r in (4, 5) else GRID
            ax.add_patch(Rectangle((0.18, y), 0.56, 0.058, facecolor=face,
                                   edgecolor=INK, linewidth=0.6, hatch=hatch))
            if r == 3:            # an adapter: a thin side path beside each block
                ax.add_patch(Rectangle((0.76, y), 0.09, 0.058, facecolor=TEAL,
                                       edgecolor=INK, linewidth=0.5))
        ax.add_patch(Rectangle((0.18, 0.0), 0.56, 0.045, facecolor=GRID,
                               edgecolor=INK, linewidth=0.6))
        ax.text(0.46, 0.022, 'patches in', ha='center', va='center', fontsize=7,
                color=INK)
        head_face = RUNG_COLOURS[r] if r >= 2 else GRID
        ax.add_patch(Rectangle((0.18, 0.925), 0.56, 0.055, facecolor=head_face,
                               edgecolor=INK, linewidth=0.8, hatch=hatch))
        ax.text(0.46, 0.952, 'head', ha='center', va='center', fontsize=7.5,
                color='white' if r >= 4 else INK)
        if r == 1:
            ax.add_patch(Rectangle((0.03, 0.1), 0.055, 0.8, facecolor=LINK_PALE,
                                   edgecolor=LINK, linewidth=0.7))
            ax.text(0.057, 0.5, 'a longer prompt', ha='center', va='center',
                    fontsize=7.5, color=LINK, rotation=90)
        name = RUNG_NAMES[r]
        if len(name) > 14:
            cut = name.rfind(' ', 0, 16)
            name = name[:cut] + '\n' + name[cut + 1:]
        else:
            name = name + '\n'
        ax.set_title(f'{r + 1}. {name}', fontsize=9.5, fontweight='bold',
                     color=INK, loc='center', pad=6)
        ax.text(0.46, -0.045, f'{counts[r]:,} numbers change', ha='center',
                va='center', fontsize=8.5, color=INK)
        start = ('the file is untouched' if r < 2 else
                 'from a random start' if r == 5 else
                 'from the pretrained numbers')
        ax.text(0.46, -0.092, start, ha='center', va='center', fontsize=7.5,
                color=MUTED)
    fig.suptitle('What each rung lets training change, in a 12-block picture model '
                 f'of {SH.whole:,} numbers', fontsize=12, fontweight='bold', y=1.05)
    _save(fig, 'ladder-what-moves.svg')


def fig_ladder_trainable_bars() -> None:
    """Log bars of how many numbers each rung trains."""
    counts = rung_trainable()
    fig, ax = plt.subplots(figsize=(9.2, 4.0))
    _plain(ax)
    ys = np.arange(6)
    drawn = [max(c, 0.6) for c in counts]
    ax.barh(ys, drawn, color=RUNG_COLOURS, edgecolor=INK, linewidth=0.7, height=0.62)
    ax.set_xscale('log')
    ax.set_xlim(0.5, 4e8)
    ax.set_yticks(ys)
    ax.set_yticklabels([f'{i + 1}. {n}' for i, n in enumerate(RUNG_NAMES)], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel('numbers training changes (logarithmic)', fontsize=10)
    for i, c in enumerate(counts):
        share = 100 * c / SH.whole
        label = 'nothing' if c == 0 else f'{c:,}  ({share:.4g}% of the model)'
        ax.text(drawn[i] * 1.5, i, label, va='center', fontsize=9, color=INK)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title('Each rung trains far more numbers than the one below it',
                 fontsize=12, fontweight='bold', loc='left')
    _save(fig, 'ladder-trainable-bars.svg')


def fig_ladder_bytes_kept() -> None:
    """Log bars of the bytes you must keep for every extra job."""
    kept = rung_kept_bytes()
    fig, ax = plt.subplots(figsize=(9.2, 4.0))
    _plain(ax)
    ys = np.arange(6)
    drawn = [max(k, 1.0) for k in kept]
    ax.barh(ys, drawn, color=RUNG_COLOURS, edgecolor=INK, linewidth=0.7, height=0.62)
    ax.set_xscale('log')
    ax.set_xlim(1, 1e10)
    ax.set_yticks(ys)
    ax.set_yticklabels([f'{i + 1}. {n}' for i, n in enumerate(RUNG_NAMES)], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel('bytes kept for each extra job (logarithmic)', fontsize=10)
    for i, k in enumerate(kept):
        if k == 0:
            txt = 'nothing at all'
        elif k < 2000:
            txt = f'{k:,.0f} bytes of prompt text'
        elif k < 2 ** 20:
            txt = f'{k / 1024:,.1f} KiB'
        else:
            txt = f'{k / 2 ** 20:,.1f} MiB'
        ax.text(drawn[i] * 1.6, i, txt, va='center', fontsize=9, color=INK)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title(f'Twenty jobs on one base model: 20 adapters are '
                 f'{20 * kept[3] / 2 ** 20:,.0f} MiB, 20 fine-tunes are '
                 f'{20 * kept[4] / 2 ** 30:,.1f} GiB',
                 fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'ladder-bytes-kept.svg')


CLIMB_AT: int = 256


def fig_climb_test(L: 'Ladder') -> None:
    """Training accuracy against held-out accuracy, by rung, at CLIMB_AT examples."""
    k = SIZES.index(CLIMB_AT)
    fig, ax = plt.subplots(figsize=(10.4, 4.6))
    _plain(ax)
    xs = np.arange(6)
    ax.bar(xs - 0.19, L.train[:, k], width=0.36, color=LINK_PALE, edgecolor=INK,
           linewidth=0.7, label=f'on the {CLIMB_AT} examples it trained on')
    ax.bar(xs + 0.19, L.test[:, k], width=0.36, color=LINK, edgecolor=INK,
           linewidth=0.7, label='on 1,500 examples held back')
    ax.axhline(L.ceiling, color=GRIP, linewidth=1.4, linestyle='--')
    ax.set_xlim(-1.62, 5.6)
    ax.text(-1.57, L.ceiling + 0.016, f'the best anything could do, {L.ceiling:.3f}',
            ha='left', fontsize=8.5, color=GRIP)
    ax.axhline(1 / TGT_CLASSES, color=MUTED, linewidth=1.0, linestyle=':')
    ax.text(-1.57, 1 / TGT_CLASSES + 0.016, f'guessing, {1 / TGT_CLASSES:.3f}',
            ha='left', fontsize=8.5, color=MUTED)
    for i in range(6):
        ax.text(i - 0.19, L.train[i, k] + 0.012, f'{L.train[i, k]:.3f}', ha='center',
                fontsize=8, color=INK)
        ax.text(i + 0.19, L.test[i, k] + 0.012, f'{L.test[i, k]:.3f}', ha='center',
                fontsize=8, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{i + 1}. {n}' for i, n in enumerate(RUNG_SHORT)], fontsize=9.5)
    ax.set_ylabel('share of answers right', fontsize=10)
    ax.set_ylim(0, 1.18)
    ax.legend(fontsize=9, loc='upper left', frameon=False, ncol=2)
    ax.set_title('The two bars say which problem you have: a short left bar means '
                 'climb, a gap means collect',
                 fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'climb-test-fit-or-data.svg')


def fig_rung_learning_curves(L: 'Ladder') -> None:
    """Held-out accuracy against the number of your own examples, by rung."""
    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    _plain(ax)
    for i in range(6):
        ax.plot(SIZES, L.test[i], marker='o', markersize=4.5, linewidth=1.9,
                color=RUNG_COLOURS[i], label=f'{i + 1}. {RUNG_NAMES[i]}')
    ax.axhline(L.ceiling, color=INK, linewidth=1.2, linestyle='--')
    ax.text(SIZES[-1], L.ceiling + 0.008, f'the best anything could do, {L.ceiling:.3f}',
            ha='right', fontsize=8.5, color=INK)
    ax.axhline(1 / TGT_CLASSES, color=MUTED, linewidth=1.0, linestyle=':')
    ax.text(SIZES[0], 1 / TGT_CLASSES + 0.008, f'guessing, {1 / TGT_CLASSES:.3f}',
            fontsize=8.5, color=MUTED)
    ax.set_xscale('log', base=2)
    ax.set_xticks(SIZES)
    ax.set_xticklabels([str(s) for s in SIZES], fontsize=9.5)
    ax.set_xlabel('your own examples', fontsize=10)
    ax.set_ylabel('share of held-out answers right', fontsize=10)
    ax.set_ylim(0.30, 0.88)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9.5, loc='upper center', bbox_to_anchor=(0.5, -0.12),
              frameon=False, ncol=3)
    ax.set_title(f'Six rungs on one simulated job, averaged over {SEEDS} worlds',
                 fontsize=12, fontweight='bold', loc='left')
    _save(fig, 'rung-learning-curves.svg')


def fig_rung_memory() -> None:
    """Memory each rung needs, for the picture model and for the big one."""
    fig, ax1 = plt.subplots(figsize=(9.2, 4.6))
    _plain(ax1)
    xs = np.arange(6)
    fro = np.array(RUN.frozen) / 2 ** 30
    tra = np.array(RUN.trained) / 2 ** 30
    act = np.array(RUN.activations) / 2 ** 30
    ax1.bar(xs, fro, color=LINK_PALE, edgecolor=INK, linewidth=0.7, label='frozen weights')
    ax1.bar(xs, tra, bottom=fro, color=PURPLE, edgecolor=INK, linewidth=0.7,
            label='weights, gradients and optimiser state')
    ax1.bar(xs, act, bottom=fro + tra, color=JOINT, edgecolor=INK, linewidth=0.7,
            label=f'saved values for the backward pass, batch {RUN.batch}')
    for i in range(6):
        total = fro[i] + tra[i] + act[i]
        ax1.text(i, total + 0.05, f'{total:.2f}', ha='center', fontsize=8.5, color=INK)
    ax1.axhline(8.0, color=GRIP, linewidth=1.2, linestyle='--')
    ax1.text(5.4, 8.1, 'an 8 GiB card', ha='right', fontsize=8.5, color=GRIP)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([f'{i + 1}. {n}' for i, n in enumerate(RUNG_SHORT)], fontsize=9.5)
    ax1.set_ylabel('memory, GiB', fontsize=10)
    ax1.set_ylim(0, 9.2)
    ax1.legend(fontsize=8.5, loc='upper left', frameon=False)
    ax1.set_title(f'The picture model, {SH.whole / 1e6:.1f} million numbers: '
                  f'every rung fits on one small card',
                  fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'rung-memory.svg')

    fig, ax2 = plt.subplots(figsize=(5.4, 4.6))
    _plain(ax2)
    big = [RUN.big_memory_lora / 2 ** 30, RUN.big_memory_full / 2 ** 30]
    ax2.bar([0, 1], big, color=[TEAL, PURPLE], edgecolor=INK, linewidth=0.7, width=0.55)
    for i, v in enumerate(big):
        ax2.text(i, v + 1.0, f'{v:.2f} GiB', ha='center', fontsize=9, color=INK)
    ax2.axhline(24.0, color=GRIP, linewidth=1.2, linestyle='--')
    ax2.text(-0.42, 26.4, 'a 24 GiB card', ha='left', fontsize=8.5, color=GRIP)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['a rank-8 adapter', 'a full fine-tune'], fontsize=9.5)
    ax2.set_ylabel('memory, GiB', fontsize=10)
    ax2.set_ylim(0, 88)
    ax2.set_title(f'The {BIG_N / 1e9:.2f} thousand million model:\n'
                  'only the adapter fits', fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'big-model-memory.svg')


def fig_rung_arithmetic() -> None:
    """The arithmetic each rung costs for the stated run, and the seconds it takes."""
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    _plain(ax)
    ys = np.arange(6)
    drawn = [max(f, 1e9) for f in RUN.flop]
    ax.barh(ys, drawn, color=RUNG_COLOURS, edgecolor=INK, linewidth=0.7, height=0.62)
    ax.set_xscale('log')
    ax.set_xlim(1e9, 3e17)
    ax.set_yticks(ys)
    ax.set_yticklabels([f'{i + 1}. {n}' for i, n in enumerate(RUNG_NAMES)], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel('floating-point operations for the whole run (logarithmic)', fontsize=10)
    for i, f in enumerate(RUN.flop):
        if f == 0:
            txt = 'no training at all'
        else:
            secs = f / DESKTOP
            txt = (f'{f:.3g} FLOP, {secs:.1f} s' if secs >= 1
                   else f'{f:.3g} FLOP, {secs:.2f} s')
        ax.text(drawn[i] * 1.6, i, txt, va='center', fontsize=9, color=INK)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title(f'{RUN.pictures} pictures, {RUN.passes} passes, on a card sustaining '
                 f'{DESKTOP / 1e12:.0f} million million operations a second',
                 fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'rung-arithmetic.svg')


def human_hours() -> dict[str, list[float]]:
    """The hours a person spends at each rung, at the stated rates."""
    collect = RUN.pictures / PICTURES_AN_HOUR
    return {
        'writing the prompt or the code': [1.0, 2.0, 3.0, 5.0, 6.0, 10.0],
        'collecting and checking examples': [0.5, 0.5, collect + 1.5, collect + 1.5,
                                             collect + 1.5, collect + 1.5],
        'running it and judging it': [0.5, 1.0, 2.0, 4.0, 6.0, 10.0],
    }


def fig_rung_human_hours() -> None:
    """Stacked human hours against machine minutes, by rung."""
    hours = human_hours()
    fig, ax = plt.subplots(figsize=(10.2, 4.6))
    _plain(ax)
    xs = np.arange(6)
    bottom = np.zeros(6)
    for (label, vals), colour in zip(hours.items(), (LINK_PALE, LINK, PURPLE)):
        ax.bar(xs, vals, bottom=bottom, color=colour, edgecolor=INK, linewidth=0.7,
               label=label)
        bottom = bottom + np.array(vals)
    machine = np.array(RUN.flop) / DESKTOP / 3600.0
    ax.plot(xs, machine, marker='o', color=GRIP, linewidth=1.8,
            label=f'the machine time, which never passes '
                  f'{machine.max() * 60:.1f} minutes')
    for i in range(6):
        ax.text(i, bottom[i] + 0.4, f'{bottom[i]:.1f} h', ha='center', fontsize=9,
                color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{i + 1}. {n}' for i, n in enumerate(RUNG_SHORT)], fontsize=9.5)
    ax.set_ylabel('hours', fontsize=10)
    ax.set_ylim(0, bottom.max() + 4)
    ax.legend(fontsize=9, loc='upper left', frameon=False)
    ax.set_title('At this model size the cost is a person\'s time, not the machine\'s',
                 fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'rung-human-hours.svg')


def fig_from_nothing_days() -> None:
    """Days of training from nothing, for three model sizes and four machine counts."""
    setups = [('1 desktop card', DESKTOP, 1), ('1 rented accelerator', RENTED, 1),
              ('64 rented', RENTED, 64), ('512 rented', RENTED, 512)]
    fig, ax = plt.subplots(figsize=(10.6, 4.8))
    _plain(ax)
    width = 0.2
    xs = np.arange(3)
    for j, (label, rate, cards) in enumerate(setups):
        vals = [PRE.days(f, rate, cards) for f in PRE.flops]
        ax.bar(xs + (j - 1.5) * width, vals, width=width, edgecolor=INK, linewidth=0.6,
               color=[LINK_PALE, LINK, PURPLE, TEAL][j], label=label)
        for i, v in enumerate(vals):
            if v >= 100:
                shown = f'{v:,.0f}'
            elif v >= 1:
                shown = f'{v:,.1f}'
            else:
                shown = f'{v:.2f}'
            ax.text(xs[i] + (j - 1.5) * width, v * 1.2, shown, ha='center',
                    fontsize=7.5, color=INK, rotation=90)
    ax.axhline(7, color=GRIP, linewidth=1.3, linestyle='--')
    ax.text(-0.82, 9.0, 'one week', ha='left', fontsize=8.5, color=GRIP)
    ax.axhline(365.25, color=GRIP, linewidth=1.0, linestyle=':')
    ax.text(-0.82, 470, 'one year', ha='left', fontsize=8.5, color=GRIP)
    ax.set_yscale('log')
    ax.set_ylim(0.002, 2e8)
    ax.set_xlim(-0.85, 2.55)
    ax.set_xticks(xs)
    ax.set_xticklabels(PRE.names, fontsize=9.5)
    ax.set_ylabel('days of training (logarithmic)', fontsize=10)
    ax.legend(fontsize=9, loc='upper left', frameon=False, ncol=2)
    ax.set_title('The arithmetic of training from nothing, at '
                 f'{DESKTOP / 1e12:.0f} and {RENTED / 1e12:.0f} million million '
                 'operations a second', fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'from-nothing-days.svg')


def fig_from_nothing_data() -> None:
    """The human time behind a pretraining set, and what one year of collecting buys."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 4.4),
                                   gridspec_kw={'width_ratios': [1, 1.1]})
    _plain(ax1)
    bars = [RUN.pictures, PRE.year_pictures, PRE.small_pictures]
    names = [f'your {RUN.pictures}\npictures', 'one person,\none year',
             'the pretraining\nset']
    ax1.bar([0, 1, 2], bars, color=[LINK, PURPLE, GRIP], edgecolor=INK, linewidth=0.7,
            width=0.6)
    ax1.set_yscale('log')
    ax1.set_ylim(100, 6e6)
    for i, v in enumerate(bars):
        ax1.text(i, v * 1.5, f'{v:,.0f}', ha='center', fontsize=9, color=INK)
    ax1.set_xticks([0, 1, 2])
    ax1.set_xticklabels(names, fontsize=9)
    ax1.set_ylabel('pictures (logarithmic)', fontsize=10)
    ax1.set_title(f'The pretraining set is\n'
                  f'{PRE.small_pictures / RUN.pictures:,.0f} times your run',
                  fontsize=11, fontweight='bold', loc='left')

    _plain(ax2)
    hours = [RUN.pictures / PICTURES_AN_HOUR, PRE.working_year, PRE.small_hours]
    ax2.barh([0, 1, 2], hours, color=[LINK, PURPLE, GRIP], edgecolor=INK, linewidth=0.7,
             height=0.55)
    for i, v in enumerate(hours):
        shown = f'{v:,.1f}' if v < 100 else f'{v:,.0f}'
        ax2.text(v + 180, i, f'{shown} hours' + (f' = {v / PRE.working_year:.1f} '
                 f'working years' if v > PRE.working_year else ''), va='center',
                 fontsize=9, color=INK)
    ax2.set_yticks([0, 1, 2])
    ax2.set_yticklabels(names, fontsize=9)
    ax2.set_xlim(0, 9000)
    ax2.set_xlabel(f'hours of a person, at {PICTURES_AN_HOUR:.0f} pictures an hour',
                   fontsize=10)
    ax2.invert_yaxis()
    ax2.grid(axis='x', color=GRID, linewidth=0.6)
    ax2.set_axisbelow(True)
    ax2.set_title('The data, not the arithmetic, is what\nyou cannot buy back',
                  fontsize=11, fontweight='bold', loc='left')
    fig.subplots_adjust(wspace=0.32)
    _save(fig, 'from-nothing-data.svg')


def fig_budget_buys(budget: dict[str, float]) -> None:
    """What one stated budget of accelerator time buys at each rung."""
    fig, ax1 = plt.subplots(figsize=(5.4, 4.6))
    _plain(ax1)
    share = budget['share_of_pretrain']
    ax1.bar([0], [100], color=GRID, edgecolor=INK, linewidth=0.7, width=0.5)
    ax1.bar([0], [share], color=GRIP, edgecolor=INK, linewidth=0.7, width=0.5)
    ax1.set_xlim(-1.0, 0.55)
    ax1.set_xticks([0])
    ax1.set_xticklabels(['one pretraining run\nof the big model'], fontsize=9.5)
    ax1.set_ylabel('per cent of the run paid for', fontsize=10)
    ax1.set_ylim(0, 112)
    ax1.annotate(f'your 200 hours\nbuy {share:.4f}%', xy=(-0.24, 0.4),
                 xytext=(-0.95, 30), fontsize=9.5, color=GRIP,
                 arrowprops=dict(arrowstyle='->', color=GRIP, linewidth=1.1))
    ax1.set_title('200 accelerator-hours against\none pretraining run', fontsize=11,
                  fontweight='bold', loc='left')
    _save(fig, 'budget-against-pretrain.svg')

    fig, ax2 = plt.subplots(figsize=(9.0, 3.6))
    _plain(ax2)
    vals = [budget['full_runs'], budget['adapter_runs'], budget['probe_runs']]
    labels = ['full fine-tunes', 'adapter runs', 'frozen-feature probes']
    ax2.barh([0, 1, 2], vals, color=[PURPLE, TEAL, LINK], edgecolor=INK, linewidth=0.7,
             height=0.55)
    ax2.set_xscale('log')
    ax2.set_xlim(1e4, 4e7)
    for i, v in enumerate(vals):
        ax2.text(v * 1.3, i, f'{v:,.0f}', va='center', fontsize=9.5, color=INK)
    ax2.set_yticks([0, 1, 2])
    ax2.set_yticklabels(labels, fontsize=9.5)
    ax2.invert_yaxis()
    ax2.set_xlabel(f'how many of them the same 200 hours buy, on the '
                   f'{SH.whole / 1e6:.1f} million number model (logarithmic)',
                   fontsize=9.5)
    ax2.grid(axis='x', color=GRID, linewidth=0.6)
    ax2.set_axisbelow(True)
    ax2.set_title('The same 200 accelerator-hours, spent on the rungs below',
                  fontsize=11, fontweight='bold', loc='left')
    _save(fig, 'budget-buys.svg')


def fig_small_model_exception() -> None:
    """The one model you can train from nothing, beside the ones you cannot."""
    items = [(f'a {PRE.tiny_n / 1e6:.0f} million number model\non '
              f'{PRE.tiny_examples:,} examples', PRE.tiny_flop, SLIDE),
             ('one full fine-tune of\nthe picture model', RUN.flop[4], PURPLE),
             ('pretraining the picture\nmodel from nothing', PRE.small_flop, JOINT),
             ('pretraining the big\nmodel from nothing', PRE.big_flop, GRIP)]
    fig, ax = plt.subplots(figsize=(10.0, 4.2))
    _plain(ax)
    ys = np.arange(len(items))
    ax.barh(ys, [f for _, f, _ in items], color=[c for *_, c in items], edgecolor=INK,
            linewidth=0.7, height=0.6)
    ax.set_xscale('log')
    ax.set_xlim(1e11, 1e25)
    for i, (_, f, _) in enumerate(items):
        secs = f / DESKTOP
        if secs < 60:
            when = f'{secs:.1f} seconds'
        elif secs < 86400:
            when = f'{secs / 60:.1f} minutes'
        elif secs < 86400 * 365:
            when = f'{secs / 86400:.1f} days'
        else:
            when = f'{secs / 86400 / 365.25:,.1f} years'
        ax.text(f * 2.5, i, f'{f:.3g} FLOP, {when} on one desktop card', va='center',
                fontsize=9, color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([n for n, *_ in items], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('floating-point operations (logarithmic)', fontsize=10)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title('A small model on your own examples is the one thing on this chart '
                 'you can finish today', fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'small-model-exception.svg')


def fig_own_score_against_worth(C: 'Candidates') -> None:
    """Two scatters: a model's own score, and its overlap, against its worth here."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.6))
    names = [chr(65 + i) for i in range(CANDIDATES)]
    for ax, xvals, xlabel, r, title in (
            (ax1, C.own_a, 'its own score, on its own job', C.r_own,
             'Its published score says almost nothing'),
            (ax2, C.overlap_a, 'how well its features carry what our job needs',
             C.r_overlap, 'How close its job was to ours says nearly everything')):
        _plain(ax)
        ax.scatter(xvals, C.ft_a, s=70, color=LINK, edgecolor=INK, linewidth=0.7,
                   zorder=3)
        for i, n in enumerate(names):
            ax.annotate(n, (xvals[i], C.ft_a[i]), textcoords='offset points',
                        xytext=(7, 4), fontsize=9, color=INK)
        fit = np.polyfit(xvals, C.ft_a, 1)
        grid_x = np.linspace(xvals.min(), xvals.max(), 50)
        ax.plot(grid_x, np.polyval(fit, grid_x), color=GRIP, linewidth=1.4,
                linestyle='--')
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel('what it reaches on our job after a\nfine-tune on 512 examples',
                      fontsize=10)
        ax.set_ylim(0.58, 0.78)
        ax.margins(x=0.13)
        ax.grid(color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.set_title(f'{title} (r = {r:+.3f})', fontsize=11, fontweight='bold',
                     loc='left')
    fig.subplots_adjust(wspace=0.3)
    _save(fig, 'own-score-against-worth.svg')


def fig_probe_predicts(C: 'Candidates') -> None:
    """The cheap probe against the expensive fine-tune, candidate by candidate."""
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    _plain(ax)
    ax.scatter(C.probe_a, C.ft_a, s=80, color=TEAL, edgecolor=INK, linewidth=0.7,
               zorder=3)
    order = np.argsort(C.probe_a)
    for j, i in enumerate(order):
        near = j > 0 and abs(C.probe_a[i] - C.probe_a[order[j - 1]]) < 0.005
        ax.annotate(chr(65 + i), (C.probe_a[i], C.ft_a[i]), textcoords='offset points',
                    xytext=(8, 6) if near else (8, -8), fontsize=10, color=INK)
    ax.plot(C.probe_a[order], C.ft_a[order], color=TEAL, linewidth=1.0, alpha=0.5)
    ax.scatter([C.probe_a[C.best_probe]], [C.ft_a[C.best_probe]], s=260,
               facecolor='none', edgecolor=GRIP, linewidth=1.8, zorder=4)
    ax.annotate(f'the probe picks {chr(65 + C.best_probe)};\nthe fine-tune agrees',
                (C.probe_a[C.best_probe], C.ft_a[C.best_probe]),
                textcoords='offset points', xytext=(-128, -6), fontsize=9, color=GRIP)
    ax.set_xlabel('a head on frozen features, trained on 64 of our examples '
                  '(minutes of work)', fontsize=9.5)
    ax.set_ylabel('a full fine-tune on 512 of our examples\n(hours of work)',
                  fontsize=9.5)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title(f'Seven of the eight sit in the same position in both orders '
                 f'(rank correlation {C.rho_probe:+.3f})', fontsize=11,
                 fontweight='bold', loc='left')
    _save(fig, 'probe-predicts.svg')


def fig_pick_by_score_costs(C: 'Candidates') -> None:
    """What picking by the published score costs against picking by the probe."""
    fig, ax = plt.subplots(figsize=(9.8, 4.4))
    _plain(ax)
    xs = np.arange(CANDIDATES)
    colours = [GRID] * CANDIDATES
    colours[C.best_ft] = TEAL
    if C.best_own != C.best_ft:
        colours[C.best_own] = GRIP
    ax.bar(xs, C.ft_a, color=colours, edgecolor=INK, linewidth=0.7, width=0.62)
    for i in range(CANDIDATES):
        ax.text(i, C.ft_a[i] + 0.004, f'{C.ft_a[i]:.3f}', ha='center', fontsize=8.5,
                color=INK)
    ax.axhline(C.ceiling, color=INK, linewidth=1.1, linestyle='--')
    ax.text(CANDIDATES - 0.4, C.ceiling - 0.018,
            f'the best anything could do, {C.ceiling:.3f}', ha='right', fontsize=8.5,
            color=INK)
    ax.text(-0.35, 0.895, f'red: picking by its own published score chooses '
            f'{chr(65 + C.best_own)}, which ends {C.gap_own:.3f} lower',
            fontsize=9.5, color=GRIP)
    ax.text(-0.35, 0.866, f'teal: the frozen-feature probe chooses '
            f'{chr(65 + C.best_ft)}, which is the best of the eight',
            fontsize=9.5, color=TEAL)
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{chr(65 + i)}\n{C.own_classes[i]}-way job'
                        for i in range(CANDIDATES)], fontsize=8.5)
    ax.set_ylabel('what it reaches on our job', fontsize=10)
    ax.set_ylim(0.55, 0.93)
    ax.set_title('The eight candidates, in the order they were listed, by what they '
                 'actually reach here', fontsize=11, fontweight='bold', loc='left')
    _save(fig, 'pick-by-score-costs.svg')


def fig_cheap_test_hours(C: 'Candidates') -> None:
    """The hours each way of screening eight candidates costs a person."""
    fig, ax = plt.subplots(figsize=(9.4, 3.8))
    _plain(ax)
    ways = [f'a probe on frozen features,\n{PROBE_HOURS * 60:.0f} minutes each',
            f'a fine-tuning attempt,\n{ATTEMPT_HOURS:.0f} hours each']
    vals = [C.probe_hours, C.attempt_hours]
    ax.barh([0, 1], vals, color=[TEAL, GRIP], edgecolor=INK, linewidth=0.7, height=0.5)
    for i, v in enumerate(vals):
        ax.text(v + 0.6, i, f'{v:.1f} hours for all {CANDIDATES}', va='center',
                fontsize=9.5, color=INK)
    ax.axvline(40, color=INK, linewidth=1.1, linestyle='--')
    ax.text(40.6, 0.5, 'a working week', fontsize=9, color=INK, va='center')
    ax.set_yticks([0, 1])
    ax.set_yticklabels(ways, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 58)
    ax.set_xlabel('hours of a person\'s time, at the stated rates', fontsize=10)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title(f'Screening by probe rather than by fine-tune saves '
                 f'{C.saved_hours:.1f} hours, which is more than a working week',
                 fontsize=11, fontweight='bold', loc='left')
    _save(fig, 'cheap-test-hours.svg')


def fig_four_sets_of_terms() -> None:
    """The separate sets of terms that touch one model you put to work."""
    fig, ax = plt.subplots(figsize=(10.4, 5.0))
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    colours = [LINK_PALE, LINK, GRIP, JOINT, SLIDE]
    for i, ((name, what), colour) in enumerate(zip(TERMS, colours)):
        y = 0.76 - i * 0.158
        ax.add_patch(Rectangle((0.06, y), 0.30, 0.125, facecolor=colour,
                               edgecolor=INK, linewidth=0.9))
        ax.text(0.21, y + 0.062, name, ha='center', va='center', fontsize=10.5,
                fontweight='bold', color=INK)
        ax.text(0.39, y + 0.062, what, ha='left', va='center', fontsize=10, color=INK)
        ax.add_patch(FancyArrowPatch((0.365, y + 0.062), (0.385, y + 0.062),
                                     arrowstyle='-', color=INK, linewidth=0.8))
    ax.text(0.5, 0.94, f'{len(TERMS)} separate sets of terms reach one model you '
                        'put to work, and they do not have to agree',
            ha='center', va='center', fontsize=12, fontweight='bold', color=INK)
    ax.text(0.06, 0.035, 'Each one is a different document, written by a different '
                         'party, and each can forbid something the others allow.',
            ha='left', va='center', fontsize=9.5, color=MUTED)
    _save(fig, 'four-sets-of-terms.svg')


def fig_clause_grid() -> None:
    """A grid of clause kinds against uses, with the blocked cells counted."""
    fig, ax = plt.subplots(figsize=(10.8, 5.2))
    _blank(ax)
    rows, cols = len(CLAUSES), len(USES)
    ax.set_xlim(-0.05, cols + 1.25)
    ax.set_ylim(-1.35, rows + 0.9)
    for j, use in enumerate(USES):
        ax.text(j + 0.5, rows + 0.12, use, ha='center', va='bottom', fontsize=9,
                color=INK)
    for i, clause in enumerate(CLAUSES):
        y = rows - 1 - i
        ax.text(-0.12, y + 0.5, clause, ha='right', va='center', fontsize=9, color=INK)
        for j in range(cols):
            blocked = BLOCKS_GRID[i][j] == 1
            ax.add_patch(Rectangle((j, y), 1, 1,
                                   facecolor=GRIP if blocked else '#eaf3ea',
                                   edgecolor='white', linewidth=2.0))
            ax.text(j + 0.5, y + 0.5, 'no' if blocked else 'yes', ha='center',
                    va='center', fontsize=10.5, color='white' if blocked else SLIDE,
                    fontweight='bold')
        ax.text(cols + 0.12, y + 0.5, f'{sum(BLOCKS_GRID[i])} of {cols} uses blocked',
                ha='left', va='center', fontsize=8.5, color=INK)
    for j in range(cols):
        n = sum(row[j] for row in BLOCKS_GRID)
        ax.text(j + 0.5, -0.28, f'{n} of {rows}\nclause kinds\nblock this',
                ha='center', va='top', fontsize=8.5, color=INK)
    blocked = sum(sum(r) for r in BLOCKS_GRID)
    ax.set_title(f'Five kinds of clause against four things you might do: '
                 f'{blocked} of the {rows * cols} pairs are refusals',
                 fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'clause-grid.svg')


def fig_read_it_first() -> None:
    """The hours a project has spent by each stage, against the half hour of reading."""
    fig, ax = plt.subplots(figsize=(10.6, 4.6))
    _plain(ax)
    names = [n for n, _ in STAGES]
    hours = [h for _, h in STAGES]
    cum = np.cumsum(hours)
    xs = np.arange(len(STAGES))
    ax.bar(xs, hours, color=LINK_PALE, edgecolor=INK, linewidth=0.7, width=0.6,
           label='hours this stage costs')
    ax.plot(xs, cum, marker='o', color=PURPLE, linewidth=2.0,
            label='hours spent so far, which a refusal now throws away')
    for i, v in enumerate(cum):
        ax.text(i, v + 1.0, f'{v:.1f} h', ha='center', fontsize=8.5, color=PURPLE)
    ax.axhline(READ_TERMS_HOURS, color=GRIP, linewidth=1.5)
    ax.annotate(f'reading the terms, {READ_TERMS_HOURS:.1f} hours',
                xy=(-0.3, READ_TERMS_HOURS), xytext=(-0.42, 6.5), ha='left',
                fontsize=9, color=GRIP,
                arrowprops=dict(arrowstyle='->', color=GRIP, linewidth=1.0))
    ax.set_xticks(xs)
    ax.set_xticklabels([n.replace(' ', '\n', 1) for n in names], fontsize=8.5)
    ax.set_ylabel('hours', fontsize=10)
    ax.set_ylim(0, cum[-1] + 7)
    ax.legend(fontsize=9, loc='upper left', frameon=False)
    ax.set_title(f'Terms read at the first stage cost {READ_TERMS_HOURS:.1f} hours; '
                 f'found at the last they cost {cum[-1]:.1f}, which is '
                 f'{cum[-1] / READ_TERMS_HOURS:.0f} times more',
                 fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'read-it-first.svg')


def fig_three_jobs_ladders(J: 'Jobs') -> None:
    """Three jobs, each taken up the ladder until it stops."""
    stops = [2, 1, 3]
    titles = ['A. tell six part types\napart on a tray',
              'B. turn an instruction into\none of 20 robot calls',
              'C. pick up one soft part\nwith your own gripper']
    whys = [f'the frozen features already\nseparate six rigid parts;\n'
            f'{J.a_full:,} pictures, {J.a_hours:.1f} hours',
            'a published model already\nholds this behaviour;\n'
            'no examples, no training',
            f'the gripper and the part are\nnew to the model;\n{J.c_demos} '
            f'demonstrations, {J.c_hours:.0f} hours']
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 5.4))
    for ax, title, stop, why in zip(axes, titles, stops, whys):
        _blank(ax)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.22, 1.12)
        for r in range(6):
            y = 0.06 + r * 0.155
            on = r <= stop
            ax.add_patch(Rectangle((0.08, y), 0.60, 0.105,
                                   facecolor=RUNG_COLOURS[r] if on else 'white',
                                   edgecolor=INK if on else GRID,
                                   linewidth=1.0 if on else 0.7,
                                   linestyle='-' if on else ':'))
            ax.text(0.38, y + 0.052, f'{r + 1}. {RUNG_NAMES[r]}', ha='center',
                    va='center', fontsize=8.5,
                    color=INK if on else MUTED)
            if r == stop:
                ax.add_patch(FancyArrowPatch((0.80, y + 0.052), (0.70, y + 0.052),
                                             arrowstyle='-|>', mutation_scale=13,
                                             color=GRIP, linewidth=1.6))
                ax.text(0.82, y + 0.052, 'stop here', ha='left', va='center',
                        fontsize=9, color=GRIP, fontweight='bold')
        ax.set_title(title, fontsize=10.5, fontweight='bold', color=INK)
        ax.text(0.08, -0.14, why, ha='left', va='center', fontsize=8.5, color=INK)
    fig.suptitle('Three robot jobs, each taken up the ladder only as far as it has to go',
                 fontsize=12.5, fontweight='bold', y=1.03)
    _save(fig, 'three-jobs-ladders.svg')


def fig_three_jobs_examples(J: 'Jobs') -> None:
    """How many examples each job needs, worked out from what varies in it."""
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    def row(y: float, title: str, factors: list[tuple[str, int]], colour: str,
            tail: str) -> None:
        ax.text(0.0, y + 0.20, title, fontsize=10.5, fontweight='bold', color=INK)
        x = 0.0
        for i, (name, v) in enumerate(factors):
            ax.add_patch(Rectangle((x, y), 0.155, 0.115, facecolor=colour,
                                   edgecolor=INK, linewidth=0.8))
            ax.text(x + 0.0775, y + 0.082, str(v), ha='center', va='center',
                    fontsize=12.5, fontweight='bold', color=INK)
            ax.text(x + 0.0775, y + 0.030, name, ha='center', va='center',
                    fontsize=7.5, color=INK)
            if i < len(factors) - 1:
                ax.text(x + 0.175, y + 0.058, 'x', ha='center', va='center',
                        fontsize=11, color=INK)
            x += 0.195
        ax.text(0.0, y - 0.065, tail, fontsize=10, color=INK)

    row(0.74, 'Job A: a picture of every way a part can appear', J.a_factors, LINK_PALE,
        f'= {J.a_combinations} combinations, and two pictures of each is '
        f'{J.a_full:,} pictures, which at {PICTURES_AN_HOUR:.0f} an hour is '
        f'{J.a_hours:.1f} hours of one afternoon.')
    row(0.40, 'Job C: a demonstration of every way the task can start', J.c_factors,
        JOINT,
        f'= {J.c_combinations} combinations, and two demonstrations of each is '
        f'{J.c_demos}, which at {DEMOS_AN_HOUR:.0f} an hour is {J.c_hours:.0f} hours '
        f'at the arm.')
    ax.text(0.0, 0.17, 'Job B: no examples at all', fontsize=10.5, fontweight='bold',
            color=INK)
    ax.add_patch(Rectangle((0.0, 0.03), 0.545, 0.095, facecolor='#f2f2f2',
                           edgecolor=INK, linewidth=0.8))
    ax.text(0.2725, 0.077, f'0 examples', ha='center', va='center', fontsize=12.5,
            fontweight='bold', color=INK)
    ax.text(0.56, 0.077, f'the rung it stops on trains nothing, so the {J.b_calls} '
            f'calls\ncost a page of prompt and no collecting at all', ha='left',
            va='center', fontsize=10, color=INK)
    ax.set_title('The number of examples comes out of what varies in the job, not out '
                 'of the air', fontsize=12, fontweight='bold', loc='left')
    _save(fig, 'three-jobs-examples.svg')


def job_hours(J: 'Jobs') -> list[tuple[str, float, str]]:
    """The hours each job costs at its chosen rung and at the rungs above it."""
    collect_a = J.a_hours + 2.0
    return [
        ('A, head on frozen features', collect_a + 3.0, LINK),
        ('A, full fine-tune instead', collect_a + 14.0, PURPLE),
        ('A, from nothing instead', PRE.small_hours, GRIP),
        ('B, a prompt', 2.0, LINK_PALE),
        ('B, a fine-tune instead', J.b_examples_if_trained / 60.0 + 14.0, PURPLE),
        ('C, an adapter on a policy', J.c_hours + 8.0, TEAL),
        ('C, from nothing instead', PRE.small_hours, GRIP),
    ]


def fig_three_jobs_hours(J: 'Jobs') -> None:
    """What stopping at the right rung saves against going to the top of the ladder."""
    rows = job_hours(J)
    fig, ax = plt.subplots(figsize=(10.4, 4.6))
    _plain(ax)
    ys = np.arange(len(rows))
    ax.barh(ys, [h for _, h, _ in rows], color=[c for *_, c in rows], edgecolor=INK,
            linewidth=0.7, height=0.6)
    ax.set_xscale('log')
    ax.set_xlim(1, 2e4)
    for i, (_, h, _) in enumerate(rows):
        txt = (f'{h:.1f} hours' if h < PRE.working_year
               else f'{h:,.0f} hours = {h / PRE.working_year:.1f} working years')
        ax.text(h * 1.25, i, txt, va='center', fontsize=9, color=INK)
    ax.axvline(40, color=INK, linewidth=1.0, linestyle='--')
    ax.text(43, -0.95, 'a working week', fontsize=8.5, color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([n for n, *_ in rows], fontsize=9)
    ax.set_ylim(len(rows) - 0.4, -1.15)
    ax.set_xlabel('hours of a person\'s time, at the stated rates (logarithmic)',
                  fontsize=10)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title('Climbing a rung you do not need costs hours; climbing to the top '
                 'costs years', fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'three-jobs-hours.svg')


def fig_job_a_where_to_stop(L: 'Ladder') -> None:
    """How much the next doubling of examples buys, which says when to stop collecting."""
    fig, ax1 = plt.subplots(figsize=(8.0, 4.8))
    _plain(ax1)
    ax1.plot(SIZES, L.test[2], marker='o', color=LINK, linewidth=2.0,
             label='a head on frozen features')
    ax1.plot(SIZES, L.test[4], marker='s', color=PURPLE, linewidth=2.0,
             label='a full fine-tune')
    ax1.axhline(L.ceiling, color=INK, linewidth=1.1, linestyle='--')
    ax1.text(SIZES[0], L.ceiling + 0.008, f'the best anything could do, {L.ceiling:.3f}',
             fontsize=8.5, color=INK)
    ax1.set_xscale('log', base=2)
    ax1.set_xticks(SIZES)
    ax1.set_xticklabels([str(s) for s in SIZES], fontsize=9)
    ax1.set_xlabel('examples collected', fontsize=10)
    ax1.set_ylabel('share of held-out answers right', fontsize=10)
    ax1.set_ylim(0.3, 0.9)
    ax1.grid(color=GRID, linewidth=0.6)
    ax1.set_axisbelow(True)
    ax1.legend(fontsize=9, loc='lower right', frameon=False)
    ax1.set_title('Two rungs on the same job: one curve flattens and one does not',
                  fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'where-to-stop-curves.svg')

    fig, ax2 = plt.subplots(figsize=(9.2, 4.4))
    _plain(ax2)
    width = 0.38
    xs = np.arange(len(SIZES) - 1)
    for j, (rung, colour) in enumerate(((2, LINK), (4, PURPLE))):
        gains = np.diff(L.test[rung])
        ax2.bar(xs + (j - 0.5) * width, gains, width=width, color=colour,
                edgecolor=INK, linewidth=0.6,
                label='a head' if rung == 2 else 'a full fine-tune')
    ax2.axhline(0.01, color=GRIP, linewidth=1.2, linestyle='--')
    ax2.set_xlim(-1.75, len(SIZES) - 1.4)
    ax2.text(-1.7, 0.0115, 'a hundredth of\nthe answers', fontsize=8.5, color=GRIP)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([f'{SIZES[i]}\nto\n{SIZES[i + 1]}' for i in xs], fontsize=8)
    ax2.set_xlabel('the doubling of your own examples', fontsize=10)
    ax2.set_ylabel('what the doubling bought', fontsize=10)
    ax2.axhline(0.0, color=INK, linewidth=0.8)
    ax2.legend(fontsize=9, loc='upper right', frameon=False)
    ax2.set_title('What each doubling of the examples bought: below the line, '
                  'another\nafternoon of collecting is not worth it', fontsize=11.5,
                  fontweight='bold', loc='left')
    _save(fig, 'what-each-doubling-bought.svg')


def fig_bytes_per_weight() -> None:
    """Why one trained weight costs six times what one frozen weight costs."""
    parts_frozen = [('the weight itself', 2, LINK_PALE)]
    parts_trained = [('the weight itself', 2, LINK_PALE),
                     ('its gradient', 2, LINK),
                     ('running average of the gradient', 4, PURPLE),
                     ('running average of its square', 4, TEAL)]
    print('--- bytes for one number ---')
    print(f'a frozen number costs {BF16} bytes; a trained one costs '
          f'{TRAINED_BYTES} bytes, which is {TRAINED_BYTES // BF16} times as much')
    fig, ax = plt.subplots(figsize=(9.6, 2.9))
    _plain(ax)
    for y, parts in ((1, parts_frozen), (0, parts_trained)):
        left = 0.0
        for name, width, colour in parts:
            ax.barh([y], [width], left=left, height=0.5, color=colour, edgecolor=INK,
                    linewidth=0.8)
            ax.text(left + width / 2.0, y, f'{width}', ha='center', va='center',
                    fontsize=11, fontweight='bold', color=INK)
            ax.text(left + width / 2.0, y - 0.34, name, ha='center', va='top',
                    fontsize=8, color=MUTED, rotation=0)
            left += width
        ax.text(left + 0.25, y, f'{left:.0f} bytes', va='center', fontsize=10,
                fontweight='bold', color=INK)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['a number training changes', 'a number held still'],
                       fontsize=10)
    ax.set_ylim(-0.75, 1.45)
    ax.set_xlim(0, 14.5)
    ax.set_xlabel('bytes kept in memory for that one number', fontsize=10)
    ax.set_title(f'One trained number costs {TRAINED_BYTES // BF16} times what one '
                 f'frozen number costs', fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'bytes-per-weight.svg')


def fig_cached_features() -> None:
    """Why a head on frozen features costs one forward pass and almost nothing after."""
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    _blank(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0.6, 9.6)
    steps = [(f'{RUN.pictures} pictures', GRID,
              ''),
             ('one forward pass each,\nthrough the frozen backbone', LINK_PALE,
              f'{RUN.cache_flop:.3g} operations, '
              f'{RUN.cache_flop / DESKTOP:.2f} s, done once'),
             (f'{RUN.pictures} saved rows of\n{WIDTH} numbers', JOINT,
              f'{RUN.pictures * WIDTH:,} numbers on disk'),
             ('200 passes of the head\nover the saved rows', LINK,
              f'{RUN.head_flop:.3g} operations in all')]
    for i, (txt, colour, note) in enumerate(steps):
        y = 8.2 - 2.1 * i
        ax.add_patch(Rectangle((1.0, y), 6.2, 1.25, facecolor=colour, edgecolor=INK,
                               linewidth=0.9))
        ax.text(4.1, y + 0.62, txt, ha='center', va='center', fontsize=10, color=INK)
        if note:
            ax.text(7.45, y + 0.62, note, ha='left', va='center', fontsize=8.5,
                    color=MUTED)
        if i < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((4.1, y), (4.1, y - 0.82),
                                         arrowstyle='-|>', mutation_scale=13,
                                         color=INK, linewidth=1.2))
    ax.set_title('Why the third rung is cheap: the backbone runs once and\nthe head '
                 'trains on what it saved', fontsize=11.5, fontweight='bold',
                 loc='left')
    _save(fig, 'cached-features.svg')


def fig_gain_per_climb(L: 'Ladder') -> None:
    """What climbing each rung bought on the simulated job, at 512 examples."""
    k = SIZES.index(512)
    gains = [L.test[i, k] - L.test[i - 1, k] for i in range(1, 6)]
    names = [f'{i + 1}. {RUNG_SHORT[i]}\nfrom {i}. {RUNG_SHORT[i - 1]}'
             for i in range(1, 6)]
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    _plain(ax)
    xs = np.arange(5)
    colours = [RUNG_COLOURS[i] for i in range(1, 6)]
    ax.bar(xs, gains, width=0.56, color=colours, edgecolor=INK, linewidth=0.7)
    for i, g in enumerate(gains):
        ax.text(i, g + (0.004 if g >= 0 else -0.012), f'{g:+.3f}', ha='center',
                va='bottom' if g >= 0 else 'top', fontsize=10, color=INK)
    ax.axhline(0.0, color=INK, linewidth=0.9)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel('what the climb added, at 512 examples', fontsize=10)
    ax.set_ylim(min(gains) - 0.04, max(gains) + 0.04)
    ax.grid(axis='y', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title('Only two of the five climbs paid for themselves on this job',
                 fontsize=11.5, fontweight='bold', loc='left')
    _save(fig, 'gain-per-climb.svg')


def report_pictures(L: 'Ladder', J: 'Jobs') -> None:
    """Print the remaining numbers that only the pictures would otherwise show."""
    print('--- the numbers drawn in the pictures ---')
    print(f'one picture is {IMG} by {IMG} pixels in 3 colours, which is '
          f'{3 * IMG * IMG:,} numbers')
    counts = rung_trainable()
    kept = rung_kept_bytes()
    for i, name in enumerate(RUNG_NAMES):
        print(f'{name:27s} trains {counts[i]:>10,} '
              f'({100 * counts[i] / SH.whole:.6g}% of the model), keeps '
              f'{kept[i]:>12,.0f} bytes = {kept[i] / 1024:9.1f} KiB = '
              f'{kept[i] / 2 ** 20:7.1f} MiB')
    print(f'twenty jobs: {20 * kept[3] / 2 ** 20:,.0f} MiB of adapters against '
          f'{20 * kept[4] / 2 ** 30:,.1f} GiB of fine-tunes')
    for i, name in enumerate(RUNG_NAMES):
        print(f'{name:27s} {RUN.flop[i]:.3g} FLOP for the stated run')
    hours = human_hours()
    for i, name in enumerate(RUNG_NAMES):
        total = sum(v[i] for v in hours.values())
        print(f'{name:27s} {total:5.1f} hours of a person, against '
              f'{RUN.flop[i] / DESKTOP / 60:.2f} minutes of machine')
    print(f'collecting {RUN.pictures} pictures at {PICTURES_AN_HOUR:.0f} an hour is '
          f'{RUN.pictures / PICTURES_AN_HOUR:.1f} hours')
    print(f'the backbone pretrain is {PRE.small_pictures:,} pictures and '
          f'{PRE.small_passes} passes')
    for name, h, _ in job_hours(J):
        print(f'{name:28s} {h:8.1f} hours')
    for rung in (2, 4):
        gains = np.diff(L.test[rung])
        row = ', '.join(f'{SIZES[i]}->{SIZES[i + 1]} {g:+.3f}'
                        for i, g in enumerate(gains))
        print(f'{RUNG_NAMES[rung]:27s} gain per doubling: {row}')
    print(f'the held-out set in the simulation is 1,500 examples, and the climb test '
          f'is read at {CLIMB_AT} examples')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    SH.report()
    RUN.report()
    PRE.report()
    budget = budget_report()
    licence_report()
    jobs = Jobs()
    jobs.report()
    ladder = Ladder()
    ladder.report()
    cands = Candidates()
    cands.report()
    report_pictures(ladder, jobs)

    fig_ladder_what_moves()
    fig_ladder_trainable_bars()
    fig_ladder_bytes_kept()
    fig_climb_test(ladder)
    fig_rung_learning_curves(ladder)
    fig_gain_per_climb(ladder)
    fig_rung_memory()
    fig_bytes_per_weight()
    fig_rung_arithmetic()
    fig_cached_features()
    fig_rung_human_hours()
    fig_from_nothing_days()
    fig_from_nothing_data()
    fig_budget_buys(budget)
    fig_small_model_exception()
    fig_own_score_against_worth(cands)
    fig_probe_predicts(cands)
    fig_pick_by_score_costs(cands)
    fig_cheap_test_hours(cands)
    fig_four_sets_of_terms()
    fig_clause_grid()
    fig_read_it_first()
    fig_three_jobs_ladders(jobs)
    fig_three_jobs_examples(jobs)
    fig_three_jobs_hours(jobs)
    fig_job_a_where_to_stop(ladder)
    print(f'wrote the diagrams under {IMAGES / DOC}')


if __name__ == '__main__':
    main()
