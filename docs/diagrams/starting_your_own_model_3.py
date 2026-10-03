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

The learning experiments are simulated. Each example is 24 numbers standing in
for one reading of one object, drawn from Gaussian blobs with
numpy.random.default_rng, and a small fully connected network (24 to 32 to 24
to 6) is pretrained on a six-class source job in NumPy. The six rungs of the
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
                         'a rank-8 adapter', 'a full fine-tune', 'train from nothing']
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


def _train(p: list[Arr], x: Arr, y: Ints, steps: int, lr: float, free: list[int],
           extra: dict[str, Arr] | None = None) -> list[Arr]:
    """Momentum gradient descent on the free weights, and on the adapter if given."""
    p = [q.copy() for q in p]
    vel = [np.zeros_like(q) for q in p]
    evel = {k: np.zeros_like(v) for k, v in (extra or {}).items()}
    n = len(x)
    for _ in range(steps):
        base = _with_adapter(p, extra) if extra is not None else p
        h1, h2, z = _forward(base, x)
        dz = _softmax(z)
        dz[np.arange(n), y] -= 1.0
        dz /= n
        g: list[Arr] = [np.zeros(0)] * 6
        g[4] = h2.T @ dz
        g[5] = dz.sum(axis=0)
        dh2 = (dz @ base[4].T) * (h2 > 0)
        g[2] = h1.T @ dh2
        g[3] = dh2.sum(axis=0)
        dh1 = (dh2 @ base[2].T) * (h1 > 0)
        g[0] = x.T @ dh1
        g[1] = dh1.sum(axis=0)
        if extra is not None:
            for j, idx in enumerate((0, 2)):
                pairs = (('a', g[idx] @ extra[f'b{j}'].T),
                         ('b', extra[f'a{j}'].T @ g[idx]))
                for key, grad in pairs:
                    k = f'{key}{j}'
                    evel[k] = 0.9 * evel[k] - lr * grad
                    extra[k] = extra[k] + evel[k]
        for i in free:
            vel[i] = 0.9 * vel[i] - lr * g[i]
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
        xs, ys, _ = world.draw(1500, 'source')
        xs_t, ys_t, _ = world.draw(800, 'source')
        net = _train(_init_net(rng, OBS, PARTS), xs, ys, 700, 0.08, [0, 1, 2, 3, 4, 5])
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
        self.own_noise = rng.permutation(np.linspace(0.15, 1.10, CANDIDATES))
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
        wanted = np.zeros((2, PARTS))
        wanted[0, 0] = 1.0
        wanted[1, 1] = 1.0
        dirs = []
        for _ in range(4):
            near = rng.normal(0.0, 1.0, size=PARTS) * np.array([1, 1, 0, 0, 0, 0])
            far = rng.normal(0.0, 1.0, size=PARTS) * np.array([0, 0, 1, 1, 1, 1])
            d = (share * near / (np.linalg.norm(near) + 1e-9)
                 + (1 - share) * far / (np.linalg.norm(far) + 1e-9))
            dirs.append(d / (np.linalg.norm(d) + 1e-9))
        basis = np.array(dirs)

        def source(n: int) -> tuple[Arr, Ints]:
            parts = world.rng.normal(0.0, 1.0, size=(n, PARTS))
            y = (parts @ basis.T).argmax(axis=1)
            seen = np.concatenate(
                [parts + world.rng.normal(0.0, self.own_noise[i], size=(n, PARTS)),
                 world.rng.normal(0.0, NUISANCE_SPREAD, size=(n, NUISANCE))], axis=1)
            x = np.cos(seen @ world.mix + world.phase) + world.rng.normal(
                0.0, 0.02, size=(n, OBS))
            return x, y.astype(np.int64)

        xs, ys = source(1500)
        xs_t, ys_t = source(800)
        net = _train(_init_net(rng, OBS, 4), xs, ys, 700, 0.08, [0, 1, 2, 3, 4, 5])
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
        print(f'{"model":>6s} {"own job":>8s} {"overlap":>8s} {"probe 64":>9s} '
              f'{"tune 512":>9s}')
        for i in range(CANDIDATES):
            print(f'{chr(65 + i):>6s} {self.own[i]:8.3f} {self.overlap[i]:8.3f} '
                  f'{self.probe[i]:9.3f} {self.ft[i]:9.3f}')
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
