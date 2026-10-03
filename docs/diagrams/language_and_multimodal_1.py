"""Generate the diagrams for the first two pages of
docs/06_neural-networks/10_language-and-multimodal-models/.

    01_large-language-models.md           -> images/language-and-multimodal-models/large-language-models/
    02_post-training-a-language-model.md  -> images/language-and-multimodal-models/post-training-a-language-model/

Run with:  python3 ../docs/diagrams/language_and_multimodal_1.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints it so the two documents can quote the same values. Which data is made up
and which is measured:

  * The corpus of robot sentences is simulated. It is built from written
    templates filled in by numpy.random.default_rng(20270101), and it holds
    instructions, descriptions, runs of questions with no answers, sentences
    that say which drawer a tool is in, and sentences that give the total of a
    small sum.
  * The language model used in every next-word picture is a real but small
    model built here: an n-gram counting model of order five with Witten-Bell
    style backoff and a uniform floor, so that every word in the vocabulary
    keeps a probability above zero. It is not a transformer; it stands in for
    one so that the arithmetic can be checked by hand. Its distributions,
    its held-out surprise, its accuracy per kind of word and every answer it
    gives to a drawer question are measured by running it.
  * The subword tokeniser is also real and built here, from the most frequent
    character pieces of the same corpus, and the token counts in the
    conversation pictures are measured with it.
  * The timing and memory numbers are illustrative. They come from one stated
    rate for reading a prompt, one stated rate for writing an answer, and one
    stated set of model shapes, and the pages say so.
  * On the second page, the six candidate answers, their qualities and the
    preference pairs are simulated with the same generator. Everything run on
    them is real arithmetic: a Bradley-Terry reward model fitted by gradient
    descent, a softmax policy improved by gradient ascent against that reward
    with a KL penalty, direct preference optimisation on the same pairs, a
    REINFORCE run against an exact answer checker, and the pass-at-k formula.
  * The accuracy against working-out tokens curve is illustrative. It comes
    from a stated toy model of a six-step chain, and the page says so.
"""

import pathlib
import sys
import textwrap
from collections import Counter

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'language-and-multimodal-models')
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

LLM_DOC: str = 'large-language-models'
POST_DOC: str = 'post-training-a-language-model'

Arr = NDArray[np.float64]

# every distribution keeps this much of its mass spread over the whole
# vocabulary, which is how a real softmax behaves: no token is impossible
FLOOR_MIX: float = 0.04


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


def _box(ax: Axes, x: float, y: float, w: float, h: float, text: str,
         face: str = 'white', edge: str = INK, size: float = 10.0,
         colour: str = INK, weight: str = 'normal', lw: float = 1.1,
         family: str | None = None) -> None:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.012,rounding_size=0.03',
                                facecolor=face, edgecolor=edge, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=size,
            color=colour, weight=weight, zorder=3,
            family=family if family else 'DejaVu Sans')


def _tile(ax: Axes, x: float, y: float, w: float, h: float, text: str,
          face: str, edge: str, size: float = 9.2) -> None:
    """A plain rectangle with text in it, so that boxes never overlap."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge, lw=1.0,
                           zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=size,
            zorder=3, family='DejaVu Sans Mono')


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = INK, lw: float = 1.3) -> None:
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='-|>', color=colour, lw=lw,
                                shrinkA=0, shrinkB=0))


# ==========================================================================
# the simulated corpus
# ==========================================================================

COLOURS: list[str] = ['red', 'blue', 'green', 'yellow', 'black', 'white']
OBJECTS: list[str] = ['block', 'cup', 'bowl', 'mug', 'plate', 'jar', 'box', 'bottle']
PLACES: list[str] = ['tray', 'shelf', 'bench', 'table', 'conveyor', 'bin']
NUMWORDS: list[str] = [str(i) for i in range(1, 19)]

TOOLS: list[str] = [
    'spanner', 'screwdriver', 'pliers', 'wrench', 'hammer', 'mallet', 'chisel',
    'file', 'saw', 'drill', 'clamp', 'vice', 'caliper', 'micrometer', 'gauge',
    'ruler', 'square', 'level', 'punch', 'reamer', 'tap', 'awl', 'scriber',
    'hacksaw', 'ratchet', 'socket', 'torch', 'multimeter', 'probe', 'tweezers',
    'scalpel', 'shears', 'snips', 'crimper', 'stripper', 'brush', 'oiler',
    'grinder', 'sander', 'magnet',
]

INSTRUCTIONS: list[str] = [
    'pick up the {c} {o} and place it on the {p} .',
    'pick up the {c} {o} .',
    'move the {c} {o} to the {p} .',
    'put the {c} {o} down on the {p} .',
    'close the gripper around the {c} {o} .',
    'lift the {c} {o} off the {p} .',
    'bring me the {t} from the bench .',
    'place the {t} back on the {p} .',
]

DESCRIPTIONS: list[str] = [
    'the camera sees the {c} {o} on the {p} .',
    'the gripper closes slowly so the {o} does not slip .',
    'the arm stops when the force sensor reads too high .',
    'the {t} is heavier than the {o} .',
    'the {c} {o} sits near the edge of the {p} .',
    'the camera does not see the {c} {o} on the {p} .',
]

QUESTIONS: list[str] = [
    'how do i stop the arm ?',
    'what speed should the arm use ?',
    'why does the gripper drop the {o} ?',
    'where is the {t} kept ?',
    'is the {c} {o} on the {p} ?',
    'how do i move the arm by hand ?',
    'what does the force sensor read ?',
    'how do i know the gripper is closed ?',
]


def _zipf_weights(n: int, s: float = 1.0) -> Arr:
    w = 1.0 / np.power(np.arange(1, n + 1), s)
    return w / w.sum()


class Corpus:
    """The simulated corpus, its word counts and the facts hidden inside it."""

    def __init__(self, rng: np.random.Generator, n_sentences: int = 30000) -> None:
        self.rng = rng
        self.obj_w: Arr = _zipf_weights(len(OBJECTS), 1.1)
        self.col_w: Arr = _zipf_weights(len(COLOURS), 0.9)
        self.place_w: Arr = _zipf_weights(len(PLACES), 0.8)
        self.tool_w: Arr = _zipf_weights(len(TOOLS), 0.8)
        # every tool lives in one drawer, and drawer 3 holds several of the
        # tools that are talked about most, which is why the model's fallback
        # answer is 3
        self.drawer: dict[str, int] = {}
        for i, t in enumerate(TOOLS):
            self.drawer[t] = int(rng.integers(1, 10))
        for t in TOOLS[:3]:
            self.drawer[t] = 3
        # how many times each tool's drawer is stated in the corpus
        self.fact_freq: dict[str, int] = {}
        freqs = [80, 60, 45, 34, 26, 20, 16, 12, 10, 8, 6, 5, 4, 3, 2, 2, 1, 1, 1, 1]
        for i, t in enumerate(TOOLS):
            self.fact_freq[t] = freqs[i] if i < len(freqs) else 0
        # the sums the corpus states, and the ones it never states
        pairs = [(a, b) for a in range(1, 10) for b in range(1, 10)]
        rng.shuffle(pairs)
        self.sum_seen: list[tuple[int, int]] = pairs[:48]
        self.sum_unseen: list[tuple[int, int]] = pairs[48:]
        self.kinds: list[str] = []
        self.sentences: list[list[str]] = []
        self._fill(n_sentences)
        self.counts: Counter[str] = Counter(w for s in self.sentences for w in s)
        self.vocab: list[str] = sorted(self.counts)
        self.n_tokens: int = sum(self.counts.values())

    # ----------------------------------------------------------------
    def _fill_slots(self, template: str) -> str:
        r = self.rng
        return (template
                .replace('{c}', COLOURS[r.choice(len(COLOURS), p=self.col_w)])
                .replace('{o}', OBJECTS[r.choice(len(OBJECTS), p=self.obj_w)])
                .replace('{p}', PLACES[r.choice(len(PLACES), p=self.place_w)])
                .replace('{t}', TOOLS[r.choice(len(TOOLS), p=self.tool_w)]))

    def _add(self, text: str, kind: str) -> None:
        self.sentences.append(text.split())
        self.kinds.append(kind)

    def _fill(self, n: int) -> None:
        r = self.rng
        # the four ordinary kinds of text, in fixed proportions
        n_inst = int(0.46 * n)
        n_desc = int(0.26 * n)
        n_ques = int(0.18 * n)
        for _ in range(n_inst):
            self._add(self._fill_slots(INSTRUCTIONS[r.integers(len(INSTRUCTIONS))]), 'instructions')
        for _ in range(n_desc):
            self._add(self._fill_slots(DESCRIPTIONS[r.integers(len(DESCRIPTIONS))]), 'descriptions')
        for _ in range(n_ques):
            run = [self._fill_slots(QUESTIONS[r.integers(len(QUESTIONS))])
                   for _ in range(int(r.integers(2, 4)))]
            self._add(' '.join(run), 'questions')
        # the drawer facts, as many times each as fact_freq says
        for t in TOOLS:
            for _ in range(self.fact_freq[t]):
                self._add(f'the {t} is in drawer {self.drawer[t]} .', 'drawer facts')
        # the sums
        for _ in range(int(0.06 * n)):
            a, b = self.sum_seen[int(r.integers(len(self.sum_seen)))]
            self._add(f'{a} plus {b} is {a + b} .', 'sums')
        order = r.permutation(len(self.sentences))
        self.sentences = [self.sentences[i] for i in order]
        self.kinds = [self.kinds[i] for i in order]

    # ----------------------------------------------------------------
    def tokens_by_kind(self) -> dict[str, int]:
        out: Counter[str] = Counter()
        for s, k in zip(self.sentences, self.kinds):
            out[k] += len(s)
        return dict(out)


class LM:
    """An n-gram counting model with backoff, used as a stand-in for a real one."""

    def __init__(self, vocab: list[str], order: int = 5) -> None:
        self.order = order
        self.vocab = list(vocab)
        self.V = len(self.vocab)
        self.ix: dict[str, int] = {w: i for i, w in enumerate(self.vocab)}
        self.cnt: list[dict[tuple[str, ...], Counter[int]]] = [dict() for _ in range(order)]
        self.tot: list[dict[tuple[str, ...], int]] = [dict() for _ in range(order)]
        self.uni: NDArray[np.float64] = np.zeros(self.V)
        self.n_uni = 0

    def add_vocab(self, words: list[str]) -> None:
        for w in words:
            if w not in self.ix:
                self.ix[w] = len(self.vocab)
                self.vocab.append(w)
        self.V = len(self.vocab)
        grown = np.zeros(self.V)
        grown[:len(self.uni)] = self.uni
        self.uni = grown

    def add_sentence(self, toks: list[str], weight: int = 1) -> None:
        pad = ['<s>'] * (self.order - 1) + toks + ['</s>']
        for w in pad:
            if w not in self.ix:
                self.add_vocab([w])
        for i in range(self.order - 1, len(pad)):
            wi = self.ix[pad[i]]
            self.uni[wi] += weight
            self.n_uni += weight
            for L in range(1, self.order):
                ctx = tuple(pad[i - L:i])
                d = self.cnt[L].setdefault(ctx, Counter())
                d[wi] += weight
                self.tot[L][ctx] = self.tot[L].get(ctx, 0) + weight

    def _base(self) -> Arr:
        p = self.uni[:self.V] / max(self.n_uni, 1)
        return 0.99 * p + 0.01 / self.V

    def _dist(self, ctx: tuple[str, ...]) -> Arr:
        if not ctx:
            return self._base()
        lower = self._dist(ctx[1:])
        d = self.cnt[len(ctx)].get(ctx)
        if d is None:
            return lower
        n = self.tot[len(ctx)][ctx]
        lam = n / (n + 3.0)
        p = np.zeros(self.V)
        for i, k in d.items():
            p[i] = k / n
        return lam * p + (1.0 - lam) * lower

    def dist(self, prompt: str | list[str]) -> Arr:
        toks = prompt.split() if isinstance(prompt, str) else list(prompt)
        pad = ['<s>'] * (self.order - 1) + toks
        ctx = tuple(pad[-(self.order - 1):])
        ctx = tuple(w if w in self.ix else '<unk>' for w in ctx)
        return (1.0 - FLOOR_MIX) * self._dist(ctx) + FLOOR_MIX * self._base()

    def p(self, prompt: str | list[str], word: str) -> float:
        d = self.dist(prompt)
        return float(d[self.ix[word]]) if word in self.ix else 0.0

    def top(self, prompt: str | list[str], k: int = 10) -> list[tuple[str, float]]:
        d = self.dist(prompt)
        order = np.argsort(-d)[:k]
        return [(self.vocab[i], float(d[i])) for i in order]

    def logprob_tokens(self, prompt: str, continuation: str) -> float:
        """Total log2 probability of a whole continuation, token by token."""
        ctx = prompt.split()
        total = 0.0
        for w in continuation.split():
            total += float(np.log2(max(self.p(ctx, w), 1e-12)))
            ctx = ctx + [w]
        return total

    def dist_with_prompt(self, ctx: list[str], prompt: list[str],
                         lam_copy: float = 0.78) -> Arr:
        """Mix the counting model with what the prompt itself says comes next.

        A real model reads its prompt and carries on a pattern it can see
        there; this mixture is the smallest honest stand-in for that.
        """
        base = self.dist(ctx)
        for L in range(min(self.order - 1, len(ctx)), 1, -1):
            suf = tuple(ctx[-L:])
            nxt = [prompt[i + L] for i in range(len(prompt) - L)
                   if tuple(prompt[i:i + L]) == suf]
            if nxt:
                p = np.zeros(self.V)
                for w in nxt:
                    if w in self.ix:
                        p[self.ix[w]] += 1.0
                if p.sum() > 0:
                    return (1.0 - lam_copy) * base + lam_copy * p / p.sum()
        return base


# ==========================================================================
# build the corpus, the model and the held-out set once
# ==========================================================================

RNG = np.random.default_rng(20270101)
CORP = Corpus(RNG, 30000)
HELD = Corpus(np.random.default_rng(777), 1200)

MODEL = LM(CORP.vocab + ['<s>', '</s>', '<unk>'])
for _s in CORP.sentences:
    MODEL.add_sentence(_s)


def _held_bits(model: LM, sentences: list[list[str]]) -> float:
    total, n = 0.0, 0
    for s in sentences:
        ctx: list[str] = []
        for w in s:
            total += -np.log2(max(model.p(ctx, w), 1e-12))
            ctx.append(w)
            n += 1
    return float(total / n)


# ==========================================================================
# a small real subword tokeniser, built from the same corpus
# ==========================================================================

class Tokeniser:
    """Greedy longest-match subword tokeniser over frequent character pieces."""

    def __init__(self, counts: Counter[str], n_pieces: int = 180) -> None:
        piece_counts: Counter[str] = Counter()
        for w, c in counts.items():
            s = '_' + w
            for L in range(2, 7):
                for i in range(len(s) - L + 1):
                    piece_counts[s[i:i + L]] += c
        chars = {ch for w in counts for ch in w} | {'_'}
        self.pieces: set[str] = set(chars) | {p for p, _ in piece_counts.most_common(n_pieces)}
        self.max_len: int = max(len(p) for p in self.pieces)

    def split_word(self, word: str) -> list[str]:
        s = '_' + word
        out: list[str] = []
        i = 0
        while i < len(s):
            for L in range(min(self.max_len, len(s) - i), 0, -1):
                if s[i:i + L] in self.pieces:
                    out.append(s[i:i + L])
                    i += L
                    break
            else:
                out.append(s[i])
                i += 1
        return out

    def split(self, text: str) -> list[str]:
        out: list[str] = []
        for w in text.split():
            if w.startswith('<|') and w.endswith('|>'):
                out.append(w)
            else:
                out.extend(self.split_word(w))
        return out

    def count(self, text: str) -> int:
        return len(self.split(text))


TOK = Tokeniser(CORP.counts, 420)


# ==========================================================================
# the illustrative cost model
# ==========================================================================

PREFILL_RATE = 7500.0    # prompt tokens read per second, illustrative
DECODE_RATE = 55.0       # answer tokens written per second, illustrative
KV_LAYERS, KV_KVHEADS, KV_HEADSIZE, KV_BYTES = 32, 8, 128, 2
KV_PER_TOKEN = 2 * KV_LAYERS * KV_KVHEADS * KV_HEADSIZE * KV_BYTES   # bytes


def answer_time(prompt_tokens: int, answer_tokens: int) -> tuple[float, float]:
    return prompt_tokens / PREFILL_RATE, answer_tokens / DECODE_RATE


# ==========================================================================
# page 1, section 1: what the model predicts
# ==========================================================================

PROMPT1 = 'pick up the red'


def next_token_distribution() -> None:
    d = MODEL.dist(PROMPT1)
    order = np.argsort(-d)
    names = [MODEL.vocab[i] for i in order[:12]]
    vals = [float(d[i]) for i in order[:12]]
    rest = float(d[order[12:]].sum())
    n_rest = MODEL.V - 12
    print(f'[s1] vocabulary size {MODEL.V} words, prompt "{PROMPT1}"')
    for nm, v in zip(names, vals):
        print(f'[s1]   {nm:12s} {v:.4f}')
    print(f'[s1]   other {n_rest} words share {rest:.4f}')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(12), vals, color=LINK, width=0.68)
    ax.bar([13], [rest], color=MUTED, width=0.68)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f'{v:.3f}', ha='center',
                fontsize=8.6, color=INK)
    ax.text(13, rest + 0.006, f'{rest:.3f}', ha='center', fontsize=8.6, color=INK)
    ax.set_xticks(list(range(12)) + [13])
    ax.set_xticklabels(names + [f'the other\n{n_rest} words'], rotation=40,
                       ha='right', fontsize=9)
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_ylabel('probability of being the next word', fontsize=10)
    ax.set_title(f'After "{PROMPT1}" the model gives every one of {MODEL.V} words a share',
                 fontsize=12.5, weight='bold')
    _save(fig, LLM_DOC, 'next-token-distribution.svg')


def whole_vocabulary() -> None:
    d = np.sort(MODEL.dist(PROMPT1))[::-1]
    cum = np.cumsum(d)
    k8 = float(cum[7])
    smallest = float(d[-1])
    print(f'[s1] top 8 words hold {k8:.4f} of the probability, '
          f'smallest word {smallest:.3e}, 1/V = {1.0 / MODEL.V:.3e}')

    fig, ax = plt.subplots(figsize=(10.0, 5.0), facecolor='white')
    _plain(ax)
    ranks = np.arange(1, len(d) + 1)
    ax.plot(ranks, d, color=LINK, lw=2)
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlabel('rank of the word, most likely first (log scale)', fontsize=10)
    ax.set_ylabel('probability (log scale)', fontsize=10)
    ax.grid(True, which='both', color=GRID, lw=0.5)
    ax2 = ax.twinx()
    ax2.plot(ranks, cum, color=GRIP, lw=2)
    ax2.set_ylim(0, 1.04)
    ax2.set_ylabel('running total of the probability', fontsize=10, color=GRIP)
    ax2.tick_params(labelsize=9.5, colors=GRIP)
    ax2.spines['top'].set_visible(False)
    ax2.annotate(f'the top 8 words hold {k8:.3f}', xy=(8, cum[7]),
                 xytext=(0.26, 0.56), textcoords='axes fraction', fontsize=10,
                 color=GRIP, arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.1))
    ax.annotate(f'the least likely word still gets {smallest:.1e}',
                xy=(len(d), d[-1]), xytext=(0.12, 0.14), textcoords='axes fraction',
                fontsize=10, color=LINK,
                arrowprops=dict(arrowstyle='-|>', color=LINK, lw=1.1))
    ax.set_title('No word gets zero: the probability is spread over the whole vocabulary',
                 fontsize=12.5, weight='bold')
    _save(fig, LLM_DOC, 'the-whole-vocabulary.svg')


def one_token_at_a_time() -> None:
    ctx = PROMPT1.split()
    rows: list[tuple[str, str, float]] = []
    joint = 1.0
    for _ in range(9):
        d = MODEL.dist(ctx)
        i = int(np.argmax(d))
        w = MODEL.vocab[i]
        if w == '</s>':
            break
        rows.append((' '.join(ctx), w, float(d[i])))
        joint *= float(d[i])
        ctx = ctx + [w]
    print(f'[s1] greedy continuation: {" ".join(ctx)}')
    print(f'[s1] joint probability of the 9 chosen words {joint:.3e}')
    for sofar, w, p in rows:
        print(f'[s1]   ...{sofar[-28:]:>28s}  ->  {w:10s} {p:.3f}')

    fig, ax = plt.subplots(figsize=(11.0, 5.6), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.4, len(rows) + 0.6)
    for r, (sofar, w, p) in enumerate(rows):
        y = len(rows) - 1 - r
        ax.text(0.015, y + 0.5, f'{r + 1}', fontsize=9.5, color=MUTED, va='center')
        ax.text(0.055, y + 0.5, '... ' + ' '.join(sofar.split()[-5:]), fontsize=10,
                color=INK, va='center', family='DejaVu Sans Mono')
        _box(ax, 0.46, y + 0.12, 0.115, 0.76, w, face=LINK_PALE, edge=LINK, size=10)
        ax.barh([y + 0.5], [p * 0.33], left=0.60, height=0.5, color=LINK)
        ax.text(0.60 + p * 0.33 + 0.008, y + 0.5, f'{p:.3f}', fontsize=9.3,
                va='center', color=INK)
    ax.text(0.055, len(rows) + 0.18, 'the text so far', fontsize=10, weight='bold')
    ax.text(0.46, len(rows) + 0.18, 'word chosen', fontsize=10, weight='bold')
    ax.text(0.60, len(rows) + 0.18, 'its probability', fontsize=10, weight='bold')
    ax.set_title('Answering is this loop: pick one word, add it to the text, work the whole thing out again',
                 fontsize=12.5, weight='bold', loc='left')
    _save(fig, LLM_DOC, 'one-token-at-a-time.svg')


# ==========================================================================
# page 1, section 2: what a lot of text teaches it
# ==========================================================================

CURVE_SIZES = [250, 500, 1000, 2000, 4000, 8000, 16000, 30000]
CURVE_BITS: list[float] = []


def more_text_lower_surprise() -> None:
    model = LM(CORP.vocab + ['<s>', '</s>', '<unk>'])
    done = 0
    held = HELD.sentences[:400]
    for n in CURVE_SIZES:
        for s in CORP.sentences[done:n]:
            model.add_sentence(s)
        done = n
        CURVE_BITS.append(_held_bits(model, held))
        print(f'[s2] trained on {n:6d} sentences -> {CURVE_BITS[-1]:.3f} bits per word, '
              f'perplexity {2 ** CURVE_BITS[-1]:.1f}')

    fig, ax = plt.subplots(figsize=(10.0, 5.2), facecolor='white')
    _plain(ax)
    ax.plot(CURVE_SIZES, CURVE_BITS, marker='o', color=LINK, lw=2.2)
    for n, b in zip(CURVE_SIZES, CURVE_BITS):
        ax.annotate(f'{b:.2f}', xy=(n, b), xytext=(0, 9), textcoords='offset points',
                    ha='center', fontsize=9, color=INK)
    ax.set_xscale('log')
    ax.set_xticks(CURVE_SIZES)
    ax.set_xticklabels([f'{n:,}' for n in CURVE_SIZES], fontsize=9)
    ax.set_xlabel('sentences of the simulated corpus used for training (log scale)', fontsize=10)
    ax.set_ylabel('surprise on held-out text\n(bits needed per word)', fontsize=10)
    ax.set_ylim(min(CURVE_BITS) - 0.35, max(CURVE_BITS) + 0.45)
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('More text, less surprise: the one number that training drives down',
                 fontsize=12.5, weight='bold')
    _save(fig, LLM_DOC, 'more-text-lower-surprise.svg')


def what_the_corpus_is_made_of() -> None:
    by_kind = CORP.tokens_by_kind()
    kinds = sorted(by_kind, key=lambda k: -by_kind[k])
    vals = [by_kind[k] for k in kinds]
    total = sum(vals)
    print(f'[s2] corpus holds {total:,} words in {len(CORP.sentences):,} sentences, '
          f'vocabulary {len(CORP.vocab)}')
    for k in kinds:
        print(f'[s2]   {k:14s} {by_kind[k]:7,d} words  ({100 * by_kind[k] / total:.1f}%)')

    fig, ax = plt.subplots(figsize=(9.8, 4.4), facecolor='white')
    _plain(ax)
    colours = [LINK, TEAL, PURPLE, JOINT, GRIP]
    ys = np.arange(len(kinds))[::-1]
    ax.barh(ys, vals, color=colours[:len(kinds)], height=0.6)
    for y, v in zip(ys, vals):
        ax.text(v + total * 0.008, y, f'{v:,} words  ({100 * v / total:.1f}%)',
                va='center', fontsize=9.5, color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels(kinds, fontsize=10)
    ax.set_xlim(0, max(vals) * 1.34)
    ax.set_xlabel('words in the simulated corpus', fontsize=10)
    ax.set_title('What the model was trained on, counted: the mixture decides what it knows',
                 fontsize=12.5, weight='bold')
    _save(fig, LLM_DOC, 'what-the-corpus-is-made-of.svg')


WORD_KINDS: dict[str, set[str]] = {
    'joining words\n(the, on, and, is)': {'the', 'on', 'and', 'is', 'it', 'to', 'a', 'in',
                                          'of', 'off', 'does', 'so', 'me', 'back', 'down',
                                          'around', 'from', 'than', 'near', 'too'},
    'verbs\n(pick, place, move)': {'pick', 'place', 'move', 'put', 'close', 'bring', 'lift',
                                   'closes', 'stops', 'sees', 'sits', 'slip', 'reads', 'use'},
    'object names\n(cup, block)': set(OBJECTS),
    'tool names\n(spanner, caliper)': set(TOOLS),
    'numbers': set(NUMWORDS),
}


def easy_and_hard_words() -> None:
    hits: Counter[str] = Counter()
    tries: Counter[str] = Counter()
    for s in HELD.sentences[:500]:
        ctx: list[str] = []
        for w in s:
            kind = next((k for k, v in WORD_KINDS.items() if w in v), None)
            if kind is not None:
                guess = MODEL.vocab[int(np.argmax(MODEL.dist(ctx)))]
                tries[kind] += 1
                hits[kind] += int(guess == w)
            ctx.append(w)
    kinds = list(WORD_KINDS)
    acc = [hits[k] / tries[k] for k in kinds]
    for k, a in zip(kinds, acc):
        print(f'[s2] {k.splitlines()[0]:16s} guessed right {100 * a:.1f}% of '
              f'{tries[k]} tries')

    fig, ax = plt.subplots(figsize=(10.2, 4.9), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(len(kinds)), [100 * a for a in acc],
                  color=[LINK, LINK, TEAL, GRIP, JOINT], width=0.62)
    for b, a, k in zip(bars, acc, kinds):
        ax.text(b.get_x() + b.get_width() / 2, 100 * a + 1.3,
                f'{100 * a:.1f}%\nof {tries[k]}', ha='center', fontsize=9.2, color=INK)
    ax.set_xticks(range(len(kinds)))
    ax.set_xticklabels(kinds, fontsize=9.3)
    ax.set_ylim(0, 100)
    ax.set_ylabel('how often the top guess was right, %', fontsize=10)
    ax.set_title('The same model is nearly certain about joining words and nearly lost about tool names',
                 fontsize=12.5, weight='bold')
    _save(fig, LLM_DOC, 'easy-and-hard-words.svg')


# ==========================================================================
# page 1, section 3: a conversation as one stream of tokens
# ==========================================================================

SYSTEM_TEXT = 'you are the controller of a robot arm . answer in one short sentence .'
CHAT: list[tuple[str, str]] = [
    ('user', 'how do i stop the arm ?'),
    ('assistant', 'press the red button on the front panel .'),
    ('user', 'is the blue cup on the tray ?'),
    ('assistant', 'yes the blue cup is on the tray .'),
    ('user', 'move it to the shelf .'),
]


def one_stream_of_tokens() -> None:
    parts: list[tuple[str, str, int]] = [('system', SYSTEM_TEXT, TOK.count(SYSTEM_TEXT) + 2)]
    for role, text in CHAT:
        parts.append((role, text, TOK.count(text) + 2))
    total = sum(p[2] for p in parts)
    print(f'[s3] the stream holds {total} tokens in {len(parts)} parts')
    for role, text, n in parts:
        print(f'[s3]   <|{role}|> {n:3d} tokens : {text}')

    fig, ax = plt.subplots(figsize=(11.4, 6.2), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.3, len(parts) + 0.9)
    face = {'system': '#ede7f8', 'user': LINK_PALE, 'assistant': '#dff0e2'}
    edge = {'system': PURPLE, 'user': LINK, 'assistant': SLIDE}
    for r, (role, text, n) in enumerate(parts):
        y = len(parts) - 1 - r
        _box(ax, 0.01, y + 0.12, 0.135, 0.74, f'<|{role}|>', face=face[role],
             edge=edge[role], size=9.6, colour=edge[role], weight='bold')
        _box(ax, 0.155, y + 0.12, 0.60, 0.74, text, face='white', edge=GRID, size=9.6)
        _box(ax, 0.765, y + 0.12, 0.09, 0.74, '<|end|>', face='#f3f3f3', edge=MUTED,
             size=9.0, colour=MUTED)
        ax.text(0.862, y + 0.5, f'{n} tokens', fontsize=9.4, va='center', color=INK)
    ax.annotate('', xy=(0.995, len(parts) - 0.55), xytext=(0.995, 0.1),
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.6))
    ax.text(0.978, len(parts) / 2 - 0.1, 'read in this order', rotation=90, fontsize=9.3,
            color=GRIP, va='center', ha='center')
    ax.set_xlim(0, 1.03)
    ax.set_title(f'A conversation is one stream of {total} tokens, with the speakers '
                 f'marked by special tokens', fontsize=12.2, weight='bold', loc='left')
    _save(fig, LLM_DOC, 'one-stream-of-tokens.svg')


def the_stream_grows() -> None:
    sys_n = TOK.count(SYSTEM_TEXT) + 2
    rng = np.random.default_rng(4242)
    user_n = [int(x) for x in rng.integers(18, 34, size=12)]
    asst_n = [int(x) for x in rng.integers(70, 140, size=12)]
    cum, read = [], []
    running = sys_n
    read_total = 0
    for i in range(12):
        running += user_n[i]
        read_total += running
        running += asst_n[i]
        cum.append(running)
        read.append(read_total)
    print(f'[s3] after 12 turns the stream is {cum[-1]} tokens long; '
          f'the model has read {read[-1]} prompt tokens in total')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.8), facecolor='white')
    _plain(ax)
    turns = np.arange(1, 13)
    ax.bar(turns, [sys_n] * 12, color=PURPLE, label='system prompt')
    ax.bar(turns, np.cumsum(user_n), bottom=[sys_n] * 12, color=LINK,
           label='all the user turns so far')
    ax.bar(turns, np.cumsum(asst_n), bottom=sys_n + np.cumsum(user_n), color=SLIDE,
           label='all the answers so far')
    ax.set_xticks(turns)
    ax.set_xlabel('turn of the conversation', fontsize=10)
    ax.set_ylabel('tokens in the stream', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='upper left')
    ax.set_ylim(0, cum[-1] * 1.30)
    ax.set_title(f'{cum[-1]} tokens by turn 12', fontsize=11.5, weight='bold')
    _plain(ax2)
    ax2.plot(turns, read, marker='o', color=GRIP, lw=2, label='tokens read, added up')
    ax2.plot(turns, cum, marker='s', color=LINK, lw=2, label='length of the stream')
    ax2.set_xticks(turns)
    ax2.set_xlabel('turn of the conversation', fontsize=10)
    ax2.set_ylabel('tokens', fontsize=10)
    ax2.legend(fontsize=9, frameon=False, loc='upper left')
    ax2.grid(True, axis='y', color=GRID, lw=0.5)
    ax2.set_title(f'{read[-1]:,} tokens read in all', fontsize=11.5, weight='bold')
    fig.suptitle('The stream only grows, and every turn reads all of it again',
                 fontsize=12.6, weight='bold', y=1.03)
    _save(fig, LLM_DOC, 'the-stream-grows.svg')


def the_window_fills() -> None:
    window = 1024
    rng = np.random.default_rng(99)
    sys_n = TOK.count(SYSTEM_TEXT) + 2
    turn_n = [int(u + a) for u, a in zip(rng.integers(18, 34, size=16),
                                         rng.integers(70, 140, size=16))]
    kept, dropped, length = [], [], []
    for t in range(1, 17):
        total = sys_n
        keep = 0
        for n in reversed(turn_n[:t]):
            if total + n <= window:
                total += n
                keep += 1
            else:
                break
        kept.append(keep)
        dropped.append(t - keep)
        length.append(sys_n + sum(turn_n[:t]))
    first_drop = next(i + 1 for i, d in enumerate(dropped) if d > 0)
    print(f'[s3] with a {window}-token window the oldest turn falls out at turn {first_drop}; '
          f'by turn 16 the conversation is {length[-1]} tokens and {dropped[-1]} turns are gone')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    turns = np.arange(1, 17)
    ax.bar(turns, kept, color=LINK, label='turns still inside the window')
    ax.bar(turns, dropped, bottom=kept, color='#dddddd', edgecolor=MUTED,
           label='turns pushed out of the window')
    ax.axvline(first_drop - 0.5, color=GRIP, lw=1.4, ls='--')
    ax.text(first_drop - 0.4, max(turns) * 0.93, f'from turn {first_drop} the oldest\nturn is dropped',
            fontsize=9.6, color=GRIP, va='top')
    ax.set_xticks(turns)
    ax.set_xlabel('turn of the conversation', fontsize=10)
    ax.set_ylabel('turns of the conversation', fontsize=10)
    ax.legend(fontsize=9.3, frameon=False, loc='upper left')
    ax.set_title(f'A {window}-token window: the conversation reaches {length[-1]} tokens and the start is lost',
                 fontsize=12.2, weight='bold')
    _save(fig, LLM_DOC, 'the-window-fills.svg')


# ==========================================================================
# page 1, section 4: hallucination
# ==========================================================================

SEEN_TOOL = TOOLS[0]
UNSEEN_TOOL = 'scalpel'
assert CORP.fact_freq[UNSEEN_TOOL] == 0


def _drawer_answer(tool: str, prompt: list[str] | None = None) -> tuple[str, float, Arr]:
    ctx = f'the {tool} is in drawer'.split()
    d = MODEL.dist_with_prompt(ctx, prompt) if prompt else MODEL.dist(ctx)
    i = int(np.argmax(d))
    return MODEL.vocab[i], float(d[i]), d


def seen_and_unseen_facts() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.2), facecolor='white')
    fig.subplots_adjust(wspace=0.30)
    for ax, tool in zip(axes, [SEEN_TOOL, UNSEEN_TOOL]):
        _plain(ax)
        top, p_top, d = _drawer_answer(tool)
        nums = [str(i) for i in range(1, 10)]
        vals = [float(d[MODEL.ix[n]]) for n in nums]
        truth = str(CORP.drawer[tool])
        colours = [SLIDE if n == truth else LINK for n in nums]
        if top != truth:
            colours = [GRIP if n == top else (SLIDE if n == truth else LINK) for n in nums]
        bars = ax.bar(range(9), vals, color=colours, width=0.64)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02, f'{v:.3f}',
                    ha='center', fontsize=8.8)
        ax.set_xticks(range(9))
        ax.set_xticklabels(nums, fontsize=10)
        ax.set_xlabel('drawer number the model would say', fontsize=10)
        ax.set_ylabel('probability', fontsize=10)
        ax.set_ylim(0, max(vals) * 1.26)
        seen = CORP.fact_freq[tool]
        right = 'right' if top == truth else 'wrong'
        ax.set_title(f'"the {tool} is in drawer ..."\nstated {seen} times in the corpus\n'
                     f'top answer {top} at {p_top:.3f}, which is {right}\n'
                     f'(the true drawer is {truth})', fontsize=10.4, weight='bold')
        print(f'[s4] {tool:12s} stated {seen:3d} times, truth {truth}, '
              f'top answer {top} at {p_top:.3f}')
    fig.suptitle('A fact the corpus never stated still gets a confident-looking answer',
                 fontsize=12.8, weight='bold', y=1.16)
    _save(fig, LLM_DOC, 'seen-and-unseen-facts.svg')


def rarer_facts_worse_answers() -> None:
    bins = [(0, 0, 'never\nstated'), (1, 5, 'stated\n1 to 5'), (6, 15, 'stated\n6 to 15'),
            (16, 40, 'stated\n16 to 40'), (41, 1000, 'stated\n41 or more')]
    acc, counts, conf = [], [], []
    for lo, hi, _ in bins:
        tools = [t for t in TOOLS if lo <= CORP.fact_freq[t] <= hi]
        right, ps = 0, []
        for t in tools:
            top, p, _ = _drawer_answer(t)
            right += int(top == str(CORP.drawer[t]))
            ps.append(p)
        acc.append(right / len(tools))
        counts.append(len(tools))
        conf.append(float(np.mean(ps)))
        print(f'[s4] {("%d-%d" % (lo, hi)):8s} {len(tools):2d} tools, '
              f'top answer right {100 * acc[-1]:.0f}%, mean top probability {conf[-1]:.3f}')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    x = np.arange(len(bins))
    ax.bar(x - 0.19, [100 * a for a in acc], width=0.36, color=SLIDE,
           label='top answer is the right drawer')
    ax.bar(x + 0.19, [100 * c for c in conf], width=0.36, color=JOINT,
           label='probability the model put on its top answer')
    for i, (a, c, n) in enumerate(zip(acc, conf, counts)):
        ax.text(i - 0.19, 100 * a + 1.6, f'{100 * a:.0f}%', ha='center', fontsize=9.2)
        ax.text(i + 0.19, 100 * c + 1.6, f'{100 * c:.0f}%', ha='center', fontsize=9.2)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{b[2]}\n({n} tools)' for b, n in zip(bins, counts)],
                       fontsize=9.3)
    ax.set_ylim(0, 108)
    ax.set_ylabel('per cent', fontsize=10)
    ax.legend(fontsize=9.3, frameon=False, loc='upper left')
    ax.set_title('Rarer facts: the answers get worse but the confidence barely moves',
                 fontsize=12.5, weight='bold')
    _save(fig, LLM_DOC, 'rarer-facts-worse-answers.svg')


def cost_of_saying_i_do_not_know() -> None:
    prompt = f'the {UNSEEN_TOOL} is in drawer'
    truth = str(CORP.drawer[UNSEEN_TOOL])
    top, _, _ = _drawer_answer(UNSEEN_TOOL)
    options = [(f'{truth} .', 'the right answer', SLIDE),
               (f'{top} .', 'a plausible wrong answer', GRIP),
               ('i do not know .', 'saying it does not know', LINK)]
    bits, labels, colours = [], [], []
    for cont, label, colour in options:
        b = -MODEL.logprob_tokens(prompt, cont)
        bits.append(b)
        labels.append(f'"{cont}"\n{label}')
        colours.append(colour)
        print(f'[s4] after "{prompt}" the continuation "{cont}" costs {b:.2f} bits')

    fig, ax = plt.subplots(figsize=(9.8, 4.8), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(3), bits, color=colours, width=0.56)
    for b, v in zip(bars, bits):
        ax.text(b.get_x() + b.get_width() / 2, v + max(bits) * 0.02, f'{v:.1f} bits',
                ha='center', fontsize=10)
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels, fontsize=9.8)
    ax.set_ylim(0, max(bits) * 1.18)
    ax.set_ylabel('training cost of writing it\n(bits of surprise, lower is better)', fontsize=10)
    ax.set_title('The objective punishes honesty: a wrong drawer number is far cheaper than "i do not know"',
                 fontsize=12.2, weight='bold')
    _save(fig, LLM_DOC, 'the-cost-of-saying-i-do-not-know.svg')


OTHER_NOTES: list[tuple[str, str]] = [
    ('the safety note', 'safety note . stop the arm with the red button before you '
                        'reach into the cell .'),
    ('the camera note', 'camera note . the camera is above the bench and sees the '
                        'whole tray .'),
    ('the gripper note', 'gripper note . the gripper closes slowly so the cup does '
                         'not slip .'),
    ('the power note', 'power note . turn the power off at the wall before you change '
                       'a tool .'),
    ('the speed note', 'speed note . use a slow speed near people .'),
    ('the tray note', 'tray note . the tray holds up to six cups .'),
    ('the bench note', 'bench note . put the tools back on the bench after use .'),
    ('the force note', 'force note . the arm stops when the force sensor reads too '
                       'high .'),
]


def _chunks() -> tuple[list[list[str]], list[str]]:
    rng = np.random.default_rng(5150)
    out, labels = [], []
    for t in TOOLS:
        place = PLACES[int(rng.integers(len(PLACES)))]
        colour = COLOURS[int(rng.integers(len(COLOURS)))]
        out.append(f'workshop note . the {t} is in drawer {CORP.drawer[t]} . '
                   f'put the {t} back on the {place} after use . '
                   f'the handle is {colour} .'.split())
        labels.append(f'the {t} note')
    for label, text in OTHER_NOTES:
        out.append(text.split())
        labels.append(label)
    return out, labels


CHUNKS, CHUNK_LABELS = _chunks()


def _retrieve(question: str, k: int = 3) -> tuple[list[int], Arr]:
    docs = [Counter(c) for c in CHUNKS]
    df = Counter()
    for d in docs:
        for w in d:
            df[w] += 1
    idf = {w: np.log((1 + len(docs)) / (1 + df[w])) + 1.0 for w in df}
    vocab = sorted(df)
    vi = {w: i for i, w in enumerate(vocab)}

    def vec(words: list[str]) -> Arr:
        v = np.zeros(len(vocab))
        for w in words:
            if w in vi:
                v[vi[w]] += idf[w]
        n = np.linalg.norm(v)
        return v / n if n > 0 else v

    q = vec(question.split())
    sims = np.array([float(q @ vec(c)) for c in CHUNKS])
    return list(np.argsort(-sims)[:k]), sims


def what_reduces_it() -> None:
    settings = ['the model\non its own', 'with the text\nretrieved',
                'allowed to\nsay no', 'retrieval and\nallowed to say no']
    thresh = 0.60
    res = []
    for mode in range(4):
        right = wrong = refused = 0
        for t in TOOLS:
            question = f'which drawer holds the {t} ?'
            prompt = None
            if mode in (1, 3):
                idx, _ = _retrieve(question)
                prompt = [w for i in idx for w in CHUNKS[i]]
            top, p, _ = _drawer_answer(t, prompt)
            if mode in (2, 3) and p < thresh:
                refused += 1
            elif top == str(CORP.drawer[t]):
                right += 1
            else:
                wrong += 1
        res.append((right, wrong, refused))
        print(f'[s4] {settings[mode].replace(chr(10), " "):36s} right {right:2d} '
              f'wrong {wrong:2d} refused {refused:2d}  (of {len(TOOLS)})')

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    _plain(ax)
    x = np.arange(4)
    r = np.array([a[0] for a in res])
    w = np.array([a[1] for a in res])
    f = np.array([a[2] for a in res])
    ax.bar(x, r, color=SLIDE, label='right answer')
    ax.bar(x, w, bottom=r, color=GRIP, label='wrong answer stated as a fact')
    ax.bar(x, f, bottom=r + w, color='#cccccc', edgecolor=MUTED, label='no answer given')
    for i in range(4):
        ax.text(i, r[i] / 2, str(r[i]), ha='center', va='center', fontsize=10, color='white')
        if w[i]:
            ax.text(i, r[i] + w[i] / 2, str(w[i]), ha='center', va='center', fontsize=10,
                    color='white')
        if f[i]:
            ax.text(i, r[i] + w[i] + f[i] / 2, str(f[i]), ha='center', va='center',
                    fontsize=10, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(settings, fontsize=9.6)
    ax.set_ylabel(f'the {len(TOOLS)} drawer questions', fontsize=10)
    ax.set_ylim(0, len(TOOLS) * 1.22)
    ax.legend(fontsize=9.3, frameon=False, loc='upper left', ncol=3)
    ax.set_title(f'Four settings on the same {len(TOOLS)} questions: the wrong-and-certain answers shrink but never reach zero',
                 fontsize=12.0, weight='bold')
    _save(fig, LLM_DOC, 'what-reduces-it.svg')


# ==========================================================================
# page 1, section 5: retrieval
# ==========================================================================

def finding_the_right_text() -> None:
    question = f'which drawer holds the {UNSEEN_TOOL} ?'
    idx, sims = _retrieve(question)
    order = np.argsort(-sims)[:12]
    print(f'[s5] question "{question}"')
    for i in order[:5]:
        print(f'[s5]   {CHUNK_LABELS[i]:22s} similarity {sims[i]:.3f}')

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    _plain(ax)
    names = [CHUNK_LABELS[i] for i in order]
    vals = [float(sims[i]) for i in order]
    colours = [JOINT if i in idx else LINK_PALE for i in order]
    ys = np.arange(len(order))[::-1]
    ax.barh(ys, vals, color=colours, edgecolor=LINK, height=0.62)
    for y, v in zip(ys, vals):
        ax.text(v + 0.006, y, f'{v:.3f}', va='center', fontsize=9.3)
    ax.set_yticks(ys)
    ax.set_yticklabels(names, fontsize=9.5)
    ax.set_xlim(0, max(vals) * 1.22)
    ax.set_xlabel('how much the chunk looks like the question (cosine similarity)', fontsize=10)
    ax.set_title(f'The question "{question}" picks its three chunks out of {len(CHUNKS)} by word overlap',
                 fontsize=12.0, weight='bold')
    _save(fig, LLM_DOC, 'finding-the-right-text.svg')


def before_and_after_retrieval() -> None:
    question = f'which drawer holds the {UNSEEN_TOOL} ?'
    idx, _ = _retrieve(question)
    prompt = [w for i in idx for w in CHUNKS[i]]
    truth = str(CORP.drawer[UNSEEN_TOOL])
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.9), facecolor='white')
    for ax, use in zip(axes, [None, prompt]):
        _plain(ax)
        top, p_top, d = _drawer_answer(UNSEEN_TOOL, use)
        nums = [str(i) for i in range(1, 10)]
        vals = [float(d[MODEL.ix[n]]) for n in nums]
        colours = [SLIDE if n == truth else LINK for n in nums]
        bars = ax.bar(range(9), vals, color=colours, width=0.64)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f'{v:.3f}', ha='center',
                    fontsize=8.4)
        ax.set_xticks(range(9))
        ax.set_xticklabels(nums, fontsize=10)
        ax.set_xlabel('drawer number', fontsize=10)
        ax.set_ylabel('probability', fontsize=10)
        ax.set_ylim(0, 1.0)
        label = ('nothing in the prompt but the question'
                 if use is None else f'{len(prompt)} retrieved words in the prompt')
        ax.set_title(f'{label}\ntop answer {top} at {p_top:.3f}, right drawer {truth} '
                     f'at {vals[int(truth) - 1]:.3f}', fontsize=11.0, weight='bold')
        print(f'[s5] {label}: top {top} at {p_top:.3f}, '
              f'truth {truth} at {vals[int(truth) - 1]:.3f}')
    fig.suptitle('The same model, the same question: the knowledge came from the prompt, not the weights',
                 fontsize=12.6, weight='bold', y=1.03)
    _save(fig, LLM_DOC, 'before-and-after-retrieval.svg')


def retrieval_accuracy_and_cost() -> None:
    plain_right = with_right = 0
    base_tokens = []
    rag_tokens = []
    for t in TOOLS:
        question = f'which drawer holds the {t} ?'
        idx, _ = _retrieve(question)
        prompt = [w for i in idx for w in CHUNKS[i]]
        top, _, _ = _drawer_answer(t)
        plain_right += int(top == str(CORP.drawer[t]))
        top2, _, _ = _drawer_answer(t, prompt)
        with_right += int(top2 == str(CORP.drawer[t]))
        base_tokens.append(TOK.count(question) + TOK.count(SYSTEM_TEXT))
        rag_tokens.append(TOK.count(question) + TOK.count(SYSTEM_TEXT)
                          + TOK.count(' '.join(prompt)))
    b, rg = float(np.mean(base_tokens)), float(np.mean(rag_tokens))
    t_b, t_r = b / PREFILL_RATE * 1000, rg / PREFILL_RATE * 1000
    print(f'[s5] accuracy over {len(TOOLS)} questions: {plain_right} right without '
          f'retrieval, {with_right} right with it')
    print(f'[s5] prompt grows from {b:.0f} to {rg:.0f} tokens, '
          f'prefill time {t_b:.1f} ms to {t_r:.1f} ms')

    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.4), facecolor='white')
    titles = ['questions answered right', 'tokens in the prompt',
              'time spent reading the prompt']
    datas = [[plain_right, with_right], [b, rg], [t_b, t_r]]
    fmts = ['{:.0f}', '{:.0f}', '{:.1f} ms']
    ylabels = [f'of {len(TOOLS)} questions', 'tokens', 'milliseconds (illustrative)']
    for ax, title, data, fmt, yl in zip(axes, titles, datas, fmts, ylabels):
        _plain(ax)
        bars = ax.bar([0, 1], data, color=[LINK, JOINT], width=0.5)
        for bb, v in zip(bars, data):
            ax.text(bb.get_x() + bb.get_width() / 2, v * 1.02, fmt.format(v),
                    ha='center', fontsize=10)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['on its own', 'with retrieval'], fontsize=9.6)
        ax.set_ylim(0, max(data) * 1.22)
        ax.set_ylabel(yl, fontsize=9.6)
        ax.set_title(title, fontsize=11.0, weight='bold')
    fig.suptitle('Retrieval buys accuracy and pays for it in prompt tokens and reading time',
                 fontsize=12.6, weight='bold', y=1.02)
    _save(fig, LLM_DOC, 'retrieval-accuracy-and-cost.svg')


# ==========================================================================
# page 1, section 6: the shape of the cost
# ==========================================================================

def reading_and_writing_time() -> None:
    cases = [('short question\n40 tokens in, 30 out', 40, 30),
             ('one page of notes\n900 tokens in, 60 out', 900, 60),
             ('long answer\n900 tokens in, 400 out', 900, 400),
             ('whole conversation\n8,000 tokens in, 200 out', 8000, 200)]
    pre, dec = [], []
    for name, pt, at in cases:
        a, b = answer_time(pt, at)
        pre.append(a)
        dec.append(b)
        print(f'[s6] {name.replace(chr(10), " "):44s} prefill {a * 1000:6.0f} ms  '
              f'decode {b * 1000:6.0f} ms  total {(a + b) * 1000:6.0f} ms')

    fig, ax = plt.subplots(figsize=(10.6, 5.1), facecolor='white')
    _plain(ax)
    x = np.arange(4)
    ax.bar(x, pre, color=LINK, label='reading the prompt')
    ax.bar(x, dec, bottom=pre, color=JOINT, label='writing the answer, one token at a time')
    for i in range(4):
        ax.text(i, pre[i] + dec[i] + 0.12, f'{(pre[i] + dec[i]):.2f} s total',
                ha='center', fontsize=9.6)
        ax.text(i, pre[i] / 2 if pre[i] > 0.25 else pre[i] + 0.04,
                f'{pre[i] * 1000:.0f} ms', ha='center', fontsize=8.8,
                color='white' if pre[i] > 0.25 else INK, va='center')
    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in cases], fontsize=9.3)
    ax.set_ylabel('seconds (illustrative rates)', fontsize=10)
    ax.set_ylim(0, max(np.array(pre) + np.array(dec)) * 1.22)
    ax.legend(fontsize=9.3, frameon=False, loc='upper left')
    ax.set_title(f'Almost all the time goes on writing: {PREFILL_RATE:,.0f} prompt tokens a second in, '
                 f'{DECODE_RATE:.0f} answer tokens a second out',
                 fontsize=11.6, weight='bold')
    _save(fig, LLM_DOC, 'reading-and-writing-time.svg')


def first_token_is_slower() -> None:
    prompt_tokens = 900
    ttft = prompt_tokens / PREFILL_RATE + 1 / DECODE_RATE
    per = 1 / DECODE_RATE
    n = 40
    times = [ttft] + [per] * (n - 1)
    print(f'[s6] with a {prompt_tokens}-token prompt the first token takes '
          f'{ttft * 1000:.0f} ms and each one after it {per * 1000:.1f} ms, '
          f'which is {ttft / per:.1f} times as long')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.6), facecolor='white')
    _plain(ax)
    ax.bar(range(1, n + 1), [t * 1000 for t in times],
           color=[GRIP] + [JOINT] * (n - 1))
    ax.annotate(f'first token {ttft * 1000:.0f} ms:\nthe whole prompt is read first',
                xy=(1, ttft * 1000), xytext=(6, ttft * 1000 * 0.85), fontsize=9.6,
                color=GRIP, arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.1))
    ax.annotate(f'every token after it {per * 1000:.1f} ms',
                xy=(20, per * 1000), xytext=(13, ttft * 1000 * 0.45), fontsize=9.6,
                color=INK, arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.1))
    ax.set_xlabel('token of the answer', fontsize=10)
    ax.set_ylabel('milliseconds (illustrative)', fontsize=10)
    ax.set_title('The first token carries the whole prompt', fontsize=11.4, weight='bold')
    _plain(ax2)
    lens = np.array([50, 200, 500, 1000, 2000, 4000, 8000, 16000, 32000])
    ttfts = lens / PREFILL_RATE * 1000 + 1 / DECODE_RATE * 1000
    ax2.plot(lens, ttfts, marker='o', color=GRIP, lw=2)
    for L, t in zip(lens, ttfts):
        if L in (50, 1000, 8000):
            ax2.annotate(f'{t:.0f} ms', xy=(L, t), xytext=(0, 10),
                         textcoords='offset points', ha='center', fontsize=9)
    ax2.annotate(f'{ttfts[-1]:.0f} ms', xy=(lens[-1], ttfts[-1]), xytext=(-46, -14),
                 textcoords='offset points', ha='center', fontsize=9)
    ax2.set_ylim(0, ttfts[-1] * 1.18)
    ax2.set_xscale('log')
    ax2.set_xticks(lens)
    ax2.set_xticklabels([f'{int(L):,}' for L in lens], rotation=40, ha='right', fontsize=8.6)
    ax2.set_xlabel('tokens in the prompt (log scale)', fontsize=10)
    ax2.set_ylabel('time to the first token, ms', fontsize=10)
    ax2.grid(True, axis='y', color=GRID, lw=0.5)
    ax2.set_title('A longer prompt pushes the first token further out',
                  fontsize=11.4, weight='bold')
    _save(fig, LLM_DOC, 'first-token-is-slower.svg')


def memory_grows_with_the_talk() -> None:
    lens = np.array([1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000])
    gb = lens * KV_PER_TOKEN / 1024 ** 3
    print(f'[s6] the stored keys and values take {KV_PER_TOKEN / 1024:.0f} KB per token '
          f'for the illustrative shapes ({KV_LAYERS} layers, {KV_KVHEADS} key-value heads, '
          f'head size {KV_HEADSIZE}, {KV_BYTES} bytes a number)')
    for L, g in zip(lens, gb):
        print(f'[s6]   {L:7,d} tokens -> {g:6.2f} GB')

    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(lens, gb, marker='o', color=PURPLE, lw=2.2)
    for L, g in zip(lens, gb):
        if L in (8000, 32000):
            ax.annotate(f'{g:.1f} GB', xy=(L, g), xytext=(-6, 10),
                        textcoords='offset points', fontsize=9.6, color=PURPLE)
    ax.annotate(f'{gb[-1]:.1f} GB', xy=(lens[-1], gb[-1]), xytext=(-52, -6),
                textcoords='offset points', fontsize=9.6, color=PURPLE)
    ax.axhline(16, color=GRIP, lw=1.3, ls='--')
    ax.set_ylim(0, 20.5)
    ax.text(1100, 17.2, 'a 16 GB board has nothing left for the weights', fontsize=9.6,
            color=GRIP)
    ax.set_xscale('log')
    ax.set_xticks(lens)
    ax.set_xticklabels([f'{int(L):,}' for L in lens], rotation=40, ha='right', fontsize=8.8)
    ax.set_xlabel('tokens held in the conversation (log scale)', fontsize=10)
    ax.set_ylabel('memory for the stored keys and values, GB', fontsize=10)
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title(f'Memory grows straight with the conversation: {KV_PER_TOKEN / 1024:.0f} KB a token (illustrative shapes)',
                 fontsize=12.0, weight='bold')
    _save(fig, LLM_DOC, 'memory-grows-with-the-talk.svg')


def inside_a_control_cycle() -> None:
    budget = 0.05
    cases = [('one control cycle\nat 20 Hz', budget, SLIDE),
             ('short reply\n40 in, 30 out', sum(answer_time(40, 30)), LINK),
             ('page of notes\n900 in, 60 out', sum(answer_time(900, 60)), LINK),
             ('long answer\n900 in, 400 out', sum(answer_time(900, 400)), JOINT),
             ('whole conversation\n8,000 in, 200 out', sum(answer_time(8000, 200)), GRIP)]
    for name, t, _ in cases[1:]:
        print(f'[s6] {name.replace(chr(10), " "):36s} {t * 1000:7.0f} ms = '
              f'{t / budget:5.1f} control cycles')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    vals = [c[1] * 1000 for c in cases]
    bars = ax.bar(range(len(cases)), vals, color=[c[2] for c in cases], width=0.56)
    for b, v, (name, t, _) in zip(bars, vals, cases):
        extra = '' if name.startswith('one control') else f'\n{t / budget:.0f} cycles'
        ax.text(b.get_x() + b.get_width() / 2, v * 1.12, f'{v:.0f} ms{extra}',
                ha='center', fontsize=9.6)
    ax.axhline(budget * 1000, color=SLIDE, lw=1.4, ls='--')
    ax.set_yscale('log')
    ax.set_xticks(range(len(cases)))
    ax.set_xticklabels([c[0] for c in cases], fontsize=9.3)
    ax.set_ylim(10, max(vals) * 4)
    ax.set_ylabel('milliseconds, log scale (illustrative)', fontsize=10)
    ax.set_title('An arm running at 20 Hz has 50 ms to decide, and every answer here is slower than that',
                 fontsize=11.8, weight='bold')
    _save(fig, LLM_DOC, 'inside-a-control-cycle.svg')


# ==========================================================================
# page 1, section 7: what these models cannot do
# ==========================================================================

def too_many_sums_to_memorise() -> None:
    digits = np.arange(1, 7)
    counts = np.array([(9 * 10 ** (d - 1)) ** 2 for d in digits], dtype=float)
    for d, c in zip(digits, counts):
        print(f'[s7] {d}-digit times {d}-digit: {int(c):,} different sums')

    fig, ax = plt.subplots(figsize=(10.0, 4.8), facecolor='white')
    _plain(ax)
    bars = ax.bar(digits, counts, color=PURPLE, width=0.56)
    for b, c in zip(bars, counts):
        ax.text(b.get_x() + b.get_width() / 2, c * 1.5, f'{int(c):,}', ha='center',
                fontsize=9.4)
    ax.set_yscale('log')
    ax.set_xticks(digits)
    ax.set_xlabel('digits in each of the two numbers', fontsize=10)
    ax.set_ylabel('different multiplications there are (log scale)', fontsize=10)
    ax.set_ylim(10, counts[-1] * 60)
    ax.set_title('Multiplication cannot be remembered: four-digit numbers already make 81 million sums',
                 fontsize=12.0, weight='bold')
    _save(fig, LLM_DOC, 'too-many-sums-to-memorise.svg')


def the_model_guesses_the_total() -> None:
    a, b = CORP.sum_unseen[0]
    ctx = f'{a} plus {b} is'.split()
    d = MODEL.dist(ctx)
    nums = [str(i) for i in range(2, 19)]
    vals = [float(d[MODEL.ix[n]]) for n in nums]
    top = nums[int(np.argmax(vals))]
    seen_right = sum(int(MODEL.vocab[int(np.argmax(MODEL.dist(f'{x} plus {y} is'.split())))]
                         == str(x + y)) for x, y in CORP.sum_seen)
    unseen_right = sum(int(MODEL.vocab[int(np.argmax(MODEL.dist(f'{x} plus {y} is'.split())))]
                           == str(x + y)) for x, y in CORP.sum_unseen)
    shown = f'{vals[a + b - 2]:.3f}' if vals[a + b - 2] >= 0.001 else 'below 0.001'
    print(f'[s7] "{a} plus {b} is" -> top answer {top} at {max(vals):.3f}, '
          f'truth {a + b} at {shown}')
    print(f'[s7] sums the corpus stated: {seen_right} of {len(CORP.sum_seen)} right; '
          f'sums it never stated: {unseen_right} of {len(CORP.sum_unseen)} right')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.7), facecolor='white',
                                  gridspec_kw={'width_ratios': [1.55, 1]})
    _plain(ax)
    colours = [SLIDE if n == str(a + b) else (GRIP if n == top else LINK) for n in nums]
    bars = ax.bar(range(len(nums)), vals, color=colours, width=0.64)
    for bb, v, n in zip(bars, vals, nums):
        if v > 0.02:
            ax.text(bb.get_x() + bb.get_width() / 2, v + 0.004, f'{v:.2f}', ha='center',
                    fontsize=8.6)
    ax.set_xticks(range(len(nums)))
    ax.set_xticklabels(nums, fontsize=9)
    ax.set_xlabel('total the model would say', fontsize=10)
    ax.set_ylabel('probability', fontsize=10)
    ax.set_title(f'"{a} plus {b} is ..." was never in the corpus: it says {top} at '
                 f'{max(vals):.2f},\nand gives the right total {a + b} {shown}',
                 fontsize=11.2, weight='bold')
    _plain(ax2)
    accs = [100 * seen_right / len(CORP.sum_seen), 100 * unseen_right / len(CORP.sum_unseen)]
    bars = ax2.bar([0, 1], accs, color=[SLIDE, GRIP], width=0.5)
    for bb, v in zip(bars, accs):
        ax2.text(bb.get_x() + bb.get_width() / 2, v + 2, f'{v:.0f}%', ha='center', fontsize=10)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels([f'the {len(CORP.sum_seen)} sums\nthe corpus stated',
                         f'the {len(CORP.sum_unseen)} sums\nit never stated'], fontsize=9.6)
    ax2.set_ylim(0, 112)
    ax2.set_ylabel('totals given right, per cent', fontsize=10)
    ax2.set_title('It knows the sums it saw\nand guesses the rest', fontsize=11.2, weight='bold')
    _save(fig, LLM_DOC, 'the-model-guesses-the-total.svg')


def counting_is_not_visible() -> None:
    words = ['screwdriver', 'conveyor', 'multimeter', 'gripper']
    rows = [(w, TOK.split_word(w)) for w in words]
    for w, ps in rows:
        print(f'[s7] "{w}" has {len(w)} letters and becomes {len(ps)} pieces: '
              f'{" | ".join(p.replace("_", "") or "_" for p in ps)}')

    fig, ax = plt.subplots(figsize=(11.0, 4.6), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.3, len(rows) + 0.5)
    for r, (w, ps) in enumerate(rows):
        y = len(rows) - 1 - r
        ax.text(0.015, y + 0.5, w, fontsize=11, va='center', family='DejaVu Sans Mono')
        x = 0.21
        for p in ps:
            txt = p.replace('_', '▁')
            wid = 0.022 + 0.019 * len(txt)
            _tile(ax, x, y + 0.14, wid, 0.7, txt, LINK_PALE, LINK, size=10.0)
            x += wid + 0.008
        ax.text(0.80, y + 0.5, f'{len(w)} letters, {len(ps)} pieces', fontsize=9.8,
                va='center', color=INK)
    ax.set_title('The model never sees letters: a word arrives as a few pieces, so counting letters is guesswork',
                 fontsize=12.0, weight='bold', loc='left')
    _save(fig, LLM_DOC, 'counting-is-not-visible.svg')


# ==========================================================================
def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    next_token_distribution()
    whole_vocabulary()
    one_token_at_a_time()
    more_text_lower_surprise()
    what_the_corpus_is_made_of()
    easy_and_hard_words()
    one_stream_of_tokens()
    the_stream_grows()
    the_window_fills()
    seen_and_unseen_facts()
    rarer_facts_worse_answers()
    cost_of_saying_i_do_not_know()
    what_reduces_it()
    finding_the_right_text()
    before_and_after_retrieval()
    retrieval_accuracy_and_cost()
    reading_and_writing_time()
    first_token_is_slower()
    memory_grows_with_the_talk()
    inside_a_control_cycle()
    too_many_sums_to_memorise()
    the_model_guesses_the_total()
    counting_is_not_visible()
    page_two()
    print(f'wrote the diagrams under {IMAGES}')


# ==========================================================================
# page 2: post-training
# ==========================================================================

ROLE_U, ROLE_A = '<|user|>', '<|assistant|>'

DEMOS: list[tuple[str, str]] = [
    ('how do i stop the arm ?', 'press the red button on the front panel .'),
    ('what speed should the arm use ?', 'use a slow speed near people .'),
    ('where is the spanner kept ?', 'the spanner is in drawer 3 .'),
    ('why does the gripper drop the cup ?', 'the grip force is too low for the cup .'),
    ('how do i move the arm by hand ?', 'hold the release button and push the arm .'),
    ('what does the force sensor read ?', 'the force sensor reads the push on the tool .'),
    ('is the blue cup on the tray ?', 'yes the blue cup is on the tray .'),
    ('how do i home the arm ?', 'press home on the panel and wait .'),
]
ANSWER_WORDS: list[str] = sorted({a.split()[0] for _, a in DEMOS})
QUESTION_WORDS: list[str] = ['how', 'what', 'why', 'where', 'is']
GOLD_Q, GOLD_A = DEMOS[0]


def _reply_mass(model: LM, question: str) -> tuple[float, float]:
    d = model.dist(f'{ROLE_U} {question} {ROLE_A}'.split())
    ans = sum(float(d[model.ix[w]]) for w in ANSWER_WORDS if w in model.ix)
    qus = sum(float(d[model.ix[w]]) for w in QUESTION_WORDS if w in model.ix)
    return ans, qus


def _mean_reply_mass(model: LM) -> tuple[float, float]:
    pairs = [_reply_mass(model, q) for q, _ in DEMOS]
    return float(np.mean([p[0] for p in pairs])), float(np.mean([p[1] for p in pairs]))


def _drawer_right(model: LM) -> int:
    right = 0
    for t in TOOLS:
        d = model.dist(f'the {t} is in drawer'.split())
        right += int(model.vocab[int(np.argmax(d))] == str(CORP.drawer[t]))
    return right


def a_question_gets_another_question(base: LM) -> None:
    prompt = GOLD_Q
    top = base.top(prompt, 10)
    print(f'[p2s1] before any tuning, after "{prompt}" the top words are:')
    for w, p in top:
        print(f'[p2s1]   {w:14s} {p:.4f}')
    q_mass = sum(p for w, p in base.top(prompt, base.V) if w in QUESTION_WORDS)
    print(f'[p2s1] question words hold {q_mass:.3f} of the next-word probability')

    fig, ax = plt.subplots(figsize=(10.2, 4.9), facecolor='white')
    _plain(ax)
    names = ['(end of text)' if w == '</s>' else w for w, _ in top]
    vals = [p for _, p in top]
    colours = [GRIP if w in QUESTION_WORDS else LINK for w, _ in top]
    bars = ax.bar(range(len(top)), vals, color=colours, width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02, f'{v:.3f}',
                ha='center', fontsize=9)
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(names, rotation=30, ha='right', fontsize=9.6)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_ylabel('probability of being the next word', fontsize=10)
    ax.set_title(f'The pretrained model answers "{prompt}" with another question:\n'
                 f'the words in red start a new question and hold {q_mass:.2f} of the probability',
                 fontsize=11.6, weight='bold')
    _save(fig, POST_DOC, 'a-question-gets-another-question.svg')


def after_instruction_tuning(tuned: LM) -> None:
    prompt = f'{ROLE_U} {GOLD_Q} {ROLE_A}'
    top = tuned.top(prompt, 10)
    print(f'[p2s2] after tuning, after "{prompt}" the top words are:')
    for w, p in top:
        print(f'[p2s2]   {w:14s} {p:.4f}')

    fig, ax = plt.subplots(figsize=(10.2, 4.9), facecolor='white')
    _plain(ax)
    names = ['(end of text)' if w == '</s>' else w for w, _ in top]
    vals = [p for _, p in top]
    colours = [SLIDE if w in ANSWER_WORDS else (GRIP if w in QUESTION_WORDS else LINK)
               for w, _ in top]
    bars = ax.bar(range(len(top)), vals, color=colours, width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02, f'{v:.3f}',
                ha='center', fontsize=9)
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(names, rotation=30, ha='right', fontsize=9.6)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_ylabel('probability of being the next word', fontsize=10)
    ax.set_title('After instruction tuning the same question starts an answer:\n'
                 f'"{GOLD_A}" begins with "{GOLD_A.split()[0]}" at '
                 f'{dict(top).get(GOLD_A.split()[0], 0.0):.3f}',
                 fontsize=11.6, weight='bold')
    _save(fig, POST_DOC, 'after-instruction-tuning.svg')


def three_stages(demo_words: int, pair_words: int) -> None:
    stages = [('pretraining\non the corpus', CORP.n_tokens, LINK),
              ('instruction tuning\non demonstrations', demo_words, SLIDE),
              ('learning from\npreference pairs', pair_words, JOINT)]
    print('[p2s1] words of text used at each stage of this script:')
    for name, n, _ in stages:
        print(f'[p2s1]   {name.replace(chr(10), " "):40s} {n:9,d} words '
              f'({100 * n / CORP.n_tokens:.2f}% of the pretraining corpus)')

    fig, ax = plt.subplots(figsize=(10.2, 4.3), facecolor='white')
    _plain(ax)
    ys = np.arange(3)[::-1]
    vals = [s[1] for s in stages]
    ax.barh(ys, vals, color=[s[2] for s in stages], height=0.58)
    for y, v in zip(ys, vals):
        ax.text(v * 1.25, y, f'{v:,} words', va='center', fontsize=10)
    ax.set_xscale('log')
    ax.set_yticks(ys)
    ax.set_yticklabels([s[0] for s in stages], fontsize=10)
    ax.set_xlim(1e2, max(vals) * 40)
    ax.set_xlabel('words of text the stage used (log scale)', fontsize=10)
    ax.set_title('The three stages in this script, by how much text each one needed',
                 fontsize=12.2, weight='bold')
    _save(fig, POST_DOC, 'three-stages.svg')


def one_demonstration() -> None:
    q_pieces = TOK.split(GOLD_Q)
    a_pieces = TOK.split(GOLD_A)
    n_all = 2 + len(q_pieces) + 1 + len(a_pieces) + 1
    print(f'[p2s2] the demonstration is {n_all} tokens, of which '
          f'{len(a_pieces) + 1} are trained on')

    seq: list[tuple[str, bool]] = ([(ROLE_U, False)] + [(p, False) for p in q_pieces]
                                   + [(ROLE_A, False)] + [(p, True) for p in a_pieces]
                                   + [('<|end|>', True)])
    fig, ax = plt.subplots(figsize=(11.6, 4.0), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    rows_y = [0.56, 0.34, 0.12]
    row, x = 0, 0.004
    for txt, trained in seq:
        label = txt.replace('_', '\u2581')
        wid = 0.018 + 0.0145 * len(label)
        if x + wid > 0.996:
            row += 1
            x = 0.004
        _tile(ax, x, rows_y[row], wid, 0.17, label,
              '#dff0e2' if trained else '#f1f1f1', SLIDE if trained else MUTED, size=8.6)
        x += wid + 0.004
    ax.text(0.004, 0.90, 'one written demonstration, cut into tokens', fontsize=11.4,
            weight='bold')
    ax.text(0.004, 0.80, 'grey: read but never scored          green: the tokens the '
            'loss is measured on', fontsize=9.8, color=INK)
    ax.text(0.004, 0.02, f'{n_all} tokens in all, {len(a_pieces) + 1} of them scored',
            fontsize=9.8, color=MUTED)
    _save(fig, POST_DOC, 'one-demonstration.svg')


def demonstrations_and_the_answer(sizes: list[int], golds: list[float],
                                  masses: list[float]) -> None:
    fig, ax = plt.subplots(figsize=(10.2, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(sizes, golds, marker='o', color=SLIDE, lw=2.2,
            label=f'probability of starting the answer with "{GOLD_A.split()[0]}"')
    ax.plot(sizes, masses, marker='s', color=LINK, lw=2.2,
            label='probability that the reply starts an answer at all')
    for n, g in zip(sizes, golds):
        ax.annotate(f'{g:.2f}', xy=(n, g), xytext=(0, -17), textcoords='offset points',
                    ha='center', fontsize=9, color=SLIDE)
    ax.set_xscale('symlog', linthresh=1)
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(n) for n in sizes], fontsize=9.5)
    ax.set_ylim(-0.08, 1.08)
    ax.set_xlabel('written demonstrations used for tuning (log scale, 0 included)', fontsize=10)
    ax.set_ylabel('probability', fontsize=10)
    ax.legend(fontsize=9.3, frameon=False, loc='lower right')
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('A few hundred demonstrations are enough to change the shape of the reply',
                 fontsize=12.2, weight='bold')
    _save(fig, POST_DOC, 'demonstrations-and-the-answer.svg')


def what_tuning_does_not_fix(before: tuple[float, float, int],
                             after: tuple[float, float, int]) -> None:
    labels = ['reply starts\nan answer', 'reply starts\nanother question',
              'drawer questions\nanswered right']
    b = [100 * before[0], 100 * before[1], 100 * before[2] / len(TOOLS)]
    a = [100 * after[0], 100 * after[1], 100 * after[2] / len(TOOLS)]
    print(f'[p2s2] before tuning: answer mass {before[0]:.3f}, question mass '
          f'{before[1]:.3f}, drawers right {before[2]}/{len(TOOLS)}')
    print(f'[p2s2] after tuning:  answer mass {after[0]:.3f}, question mass '
          f'{after[1]:.3f}, drawers right {after[2]}/{len(TOOLS)}')

    fig, ax = plt.subplots(figsize=(10.2, 4.9), facecolor='white')
    _plain(ax)
    x = np.arange(3)
    ax.bar(x - 0.19, b, width=0.36, color=MUTED, label='before instruction tuning')
    ax.bar(x + 0.19, a, width=0.36, color=SLIDE, label='after instruction tuning')
    for i, (vb, va) in enumerate(zip(b, a)):
        ax.text(i - 0.19, vb + 1.6, f'{vb:.0f}%', ha='center', fontsize=9.4)
        ax.text(i + 0.19, va + 1.6, f'{va:.0f}%', ha='center', fontsize=9.4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.6)
    ax.set_ylim(0, 112)
    ax.set_ylabel('per cent', fontsize=10)
    ax.legend(fontsize=9.3, frameon=False, loc='upper center')
    ax.set_title('Tuning changes the shape of the reply and leaves what the model knows alone',
                 fontsize=12.2, weight='bold')
    _save(fig, POST_DOC, 'what-tuning-does-not-fix.svg')




# --------------------------------------------------------------------------
# preferences: seven candidate answers, their qualities and the pairs
# --------------------------------------------------------------------------

CAND: list[tuple[str, float, float, float, float, int]] = [
    # text, right action, how much it really helps, how helpful it looks, polite, words
    ('open the gripper slowly over the tray .', 1.0, 0.9, 0.60, 0.0, 8),
    ('i am sorry about this . a robot arm can hold an object in several ways '
     'and there are many things you might want to think about first .',
     0.0, 0.10, 0.30, 1.0, 26),
    ('open the gripper .', 1.0, 0.5, 0.30, 0.0, 4),
    ('please open the gripper slowly over the tray so the cup is not dropped , '
     'and then move the arm clear .', 1.0, 1.00, 0.80, 1.0, 22),
    ('turn the power off .', 0.0, 0.20, 0.30, 0.0, 5),
    ('that is a good question and it depends on the gripper , the cup , the '
     'surface and the speed , so you should look at the manual for the arm and '
     'for the gripper and then decide what is best in your own case .',
     0.0, 0.05, 0.40, 1.0, 44),
    ('there are three things to check here . first look at the status light on '
     'the gripper , then check that the cup is clear of the tray , and then '
     'press the blue reset button twice before you move the arm back to its '
     'home position .', 0.0, 0.10, 1.00, 1.0, 52),
]
TRUE_NAMES = ['gives the right action', 'how much it really helps', 'polite wording',
              'length of the answer']
SEEN_NAMES = ['how helpful it looks', 'polite wording', 'length of the answer']
W_TRUE = np.array([2.2, 1.4, 0.35, -0.25])
LAZY_CAREFUL = 0.08     # how often a careful annotator just picks the longer answer
LAZY_HURRIED = 0.75     # how often a hurried one does


def _features() -> tuple[Arr, Arr]:
    """The four qualities that decide the true value, and the three a judge can see."""
    ft = np.zeros((len(CAND), 4))
    fr = np.zeros((len(CAND), 3))
    for i, (_, c, h, lk, p, w) in enumerate(CAND):
        ft[i] = [c, h, p, (w - 20) / 20.0]
        fr[i] = [lk, p, (w - 20) / 20.0]
    return ft, fr


FEAT_T, FEAT_R = _features()
U_TRUE = FEAT_T @ W_TRUE
THETA_REF = 1.2 * FEAT_T[:, 2] + 0.8 * FEAT_T[:, 3]
N_CAND = len(CAND)
BEST_I = int(np.argmax(U_TRUE))
HACK_I = N_CAND - 1


def _softmax(z: Arr) -> Arr:
    e = np.exp(z - z.max())
    return e / e.sum()


PI_REF = _softmax(THETA_REF)


def _make_pairs(n: int, rng: np.random.Generator, lazy: float) -> list[tuple[int, int]]:
    """Simulated preference pairs, each one (preferred, rejected)."""
    pairs = []
    for _ in range(n):
        i, j = rng.choice(N_CAND, size=2, replace=False)
        if rng.random() < lazy:
            w, l = (i, j) if CAND[i][5] >= CAND[j][5] else (j, i)
        else:
            p = 1.0 / (1.0 + np.exp(-(U_TRUE[i] - U_TRUE[j])))
            w, l = (i, j) if rng.random() < p else (j, i)
        pairs.append((int(w), int(l)))
    return pairs


CAREFUL = _make_pairs(320, np.random.default_rng(31337), LAZY_CAREFUL)
HURRIED = _make_pairs(320, np.random.default_rng(31337), LAZY_HURRIED)
TRAIN_PAIRS, TEST_PAIRS = CAREFUL[:240], CAREFUL[240:]
HURRIED_TRAIN, HURRIED_TEST = HURRIED[:240], HURRIED[240:]


def seven_answers_and_their_qualities() -> None:
    print('[p2s3] the seven candidate answers:')
    for i, (txt, c, h, lk, p, w) in enumerate(CAND):
        print(f'[p2s3]   {i}: right={c:.0f} really helps={h:.2f} looks={lk:.2f} '
              f'polite={p:.0f} words={w:2d} -> true value {U_TRUE[i]:.2f}, the model '
              f'before preferences gives it {PI_REF[i]:.3f}')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14.4, 7.6), facecolor='white',
                                  gridspec_kw={'width_ratios': [2.5, 1]})
    fig.subplots_adjust(wspace=0.34)
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, N_CAND + 0.4)
    for i, (txt, c, h, lk, p, w) in enumerate(CAND):
        y = N_CAND - 1 - i
        ax.text(0.004, y + 0.45, f'{i}', fontsize=10, color=MUTED, va='center')
        ax.text(0.040, y + 0.45, textwrap.fill(txt, 58), fontsize=8.4, va='center')
        ax.text(0.700, y + 0.45, f'a judge sees:  looks {lk:.2f},  polite {p:.0f},\n'
                f'                       {w} words\n'
                f'really true:   right {c:.0f},  helps {h:.2f}',
                fontsize=8.2, va='center', color=INK)
    ax.set_title('The seven answers the model could give',
                 fontsize=11.4, weight='bold', loc='left')
    _plain(ax2)
    ys = np.arange(N_CAND)[::-1]
    ax2.barh(ys, U_TRUE, color=[SLIDE if u > 2 else GRIP for u in U_TRUE], height=0.6)
    for y, u in zip(ys, U_TRUE):
        ax2.text(u + 0.07, y, f'{u:.2f}', va='center', fontsize=9.4)
    ax2.set_yticks(ys)
    ax2.set_yticklabels([f'answer {i}' for i in range(N_CAND)], fontsize=9.6)
    ax2.set_xlim(0, max(U_TRUE) * 1.24)
    ax2.set_xlabel('true value to the person (made-up weights)', fontsize=9.8)
    ax2.set_title('What each one is really worth', fontsize=11.4, weight='bold')
    _save(fig, POST_DOC, 'seven-answers-and-their-qualities.svg')


def a_preference_pair() -> None:
    w, l = BEST_I, HACK_I
    n_same = sum(1 for a, b in TRAIN_PAIRS if {a, b} == {w, l})
    n_right = sum(1 for a, b in TRAIN_PAIRS if a == w and b == l)
    print(f'[p2s3] of the {n_same} careful pairs that put answer {w} against answer {l}, '
          f'{n_right} preferred answer {w}')

    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.01, 0.95, 'the prompt both answers were written for', fontsize=10,
            weight='bold')
    _box(ax, 0.01, 0.78, 0.96, 0.13,
         'the arm has stopped with the cup still in the gripper . what should i do ?',
         face=LINK_PALE, edge=LINK, size=10)
    for k, (idx, label, colour, face) in enumerate(
            [(w, 'the annotator chose this one', SLIDE, '#dff0e2'),
             (l, 'and rejected this one', GRIP, '#fbe3e3')]):
        y = 0.42 - 0.38 * k
        ax.text(0.01, y + 0.30, label, fontsize=10, weight='bold', color=colour)
        _box(ax, 0.01, y, 0.70, 0.28, textwrap.fill(CAND[idx][0], 74), face=face,
             edge=colour, size=8.6)
        ax.text(0.735, y + 0.14, f'answer {idx}\n{CAND[idx][5]} words\n'
                f'before preferences: {PI_REF[idx]:.3f}\ntrue value: {U_TRUE[idx]:.2f}',
                fontsize=9.0, va='center')
    ax.set_title('One preference pair: two answers to one prompt, and which one a person preferred',
                 fontsize=12.0, weight='bold', loc='left')
    _save(fig, POST_DOC, 'a-preference-pair.svg')


def where_the_pairs_disagree() -> None:
    gaps = np.array([abs(U_TRUE[a] - U_TRUE[b]) for a, b in TRAIN_PAIRS])
    wrong = np.array([U_TRUE[a] < U_TRUE[b] for a, b in TRAIN_PAIRS])
    longer_c = np.array([CAND[a][5] > CAND[b][5] for a, b in TRAIN_PAIRS])
    longer_h = np.array([CAND[a][5] > CAND[b][5] for a, b in HURRIED_TRAIN])
    wrong_h = np.array([U_TRUE[a] < U_TRUE[b] for a, b in HURRIED_TRAIN])
    edges = [0.0, 0.4, 1.0, 3.0, 4.0]
    labels, fr, counts = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (gaps >= lo) & (gaps < hi)
        if m.sum() == 0:
            continue
        labels.append(f'{lo:.1f} to {hi:.1f}')
        fr.append(float(wrong[m].mean()))
        counts.append(int(m.sum()))
    print(f'[p2s3] careful pairs: {100 * wrong.mean():.1f}% picked the answer with the '
          f'lower true value, {100 * longer_c.mean():.1f}% picked the longer answer')
    print(f'[p2s3] hurried pairs: {100 * wrong_h.mean():.1f}% picked the answer with the '
          f'lower true value, {100 * longer_h.mean():.1f}% picked the longer answer')
    for la, f, c in zip(labels, fr, counts):
        print(f'[p2s3]   gap {la}: {c:3d} pairs, {100 * f:.0f}% picked the worse answer')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.7), facecolor='white')
    _plain(ax)
    bars = ax.bar(range(len(labels)), [100 * f for f in fr], color=GRIP, width=0.58)
    for b, f, c in zip(bars, fr, counts):
        ax.text(b.get_x() + b.get_width() / 2, 100 * f + 1.5, f'{100 * f:.0f}%\n{c} pairs',
                ha='center', fontsize=9.2)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9.4)
    ax.set_xlabel('gap in true value between the two answers', fontsize=10)
    ax.set_ylabel('pairs where the worse answer was chosen, %', fontsize=10)
    ax.set_ylim(0, 72)
    ax.set_title('Close calls are noisy, clear ones are not', fontsize=11.4, weight='bold')
    _plain(ax2)
    x = np.arange(2)
    ax2.bar(x - 0.18, [100 * longer_c.mean(), 100 * longer_h.mean()], width=0.34,
            color=JOINT, label='chose the longer answer')
    ax2.bar(x + 0.18, [100 * wrong.mean(), 100 * wrong_h.mean()], width=0.34,
            color=GRIP, label='chose the worse answer')
    for i, (a, b) in enumerate([(longer_c.mean(), wrong.mean()),
                                (longer_h.mean(), wrong_h.mean())]):
        ax2.text(i - 0.18, 100 * a + 1.4, f'{100 * a:.0f}%', ha='center', fontsize=9.4)
        ax2.text(i + 0.18, 100 * b + 1.4, f'{100 * b:.0f}%', ha='center', fontsize=9.4)
    ax2.set_xticks(x)
    ax2.set_xticklabels(['a careful annotator', 'a hurried annotator'], fontsize=9.6)
    ax2.set_ylim(0, 92)
    ax2.set_ylabel('per cent of 240 pairs', fontsize=10)
    ax2.legend(fontsize=9.2, frameon=False, loc='upper left')
    ax2.set_title('Two simulated annotators on the same answers',
                  fontsize=11.4, weight='bold')
    _save(fig, POST_DOC, 'where-the-pairs-disagree.svg')


# --------------------------------------------------------------------------
# the reward model and the policy trained against it
# --------------------------------------------------------------------------

def fit_reward_model(train: list[tuple[int, int]], test: list[tuple[int, int]],
                     steps: int = 500, lr: float = 0.6
                     ) -> tuple[Arr, list[float], list[float]]:
    w = np.zeros(FEAT_R.shape[1])
    loss_hist, acc_hist = [], []
    for _ in range(steps):
        g = np.zeros(FEAT_R.shape[1])
        loss = 0.0
        for a, b in train:
            d = FEAT_R[a] - FEAT_R[b]
            z = float(w @ d)
            s = 1.0 / (1.0 + np.exp(-z))
            loss += -np.log(max(s, 1e-12))
            g += -(1.0 - s) * d
        w -= lr * g / len(train)
        loss_hist.append(loss / len(train))
        acc_hist.append(float(np.mean([float(w @ (FEAT_R[a] - FEAT_R[b])) > 0
                                       for a, b in test])))
    return w, loss_hist, acc_hist


def the_reward_model_learns(loss_hist: list[float], acc_hist: list[float]) -> None:
    print(f'[p2s4] reward model on the careful pairs: loss fell from {loss_hist[0]:.3f} '
          f'to {loss_hist[-1]:.3f}, and it agrees with '
          f'{100 * acc_hist[-1]:.1f}% of the {len(TEST_PAIRS)} pairs held back')

    fig, ax = plt.subplots(figsize=(10.2, 4.9), facecolor='white')
    _plain(ax)
    steps = np.arange(1, len(loss_hist) + 1)
    ax.plot(steps, loss_hist, color=LINK, lw=2.2)
    ax.set_xlabel('gradient steps', fontsize=10)
    ax.set_ylabel('average loss on the training pairs', fontsize=10, color=LINK)
    ax.tick_params(axis='y', colors=LINK)
    ax.set_ylim(0, max(loss_hist) * 1.1)
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax2 = ax.twinx()
    ax2.plot(steps, [100 * a for a in acc_hist], color=SLIDE, lw=2.2)
    ax2.set_ylabel(f'pairs it gets right of the {len(TEST_PAIRS)} held back, %',
                   fontsize=10, color=SLIDE)
    ax2.tick_params(axis='y', colors=SLIDE)
    ax2.set_ylim(40, 100)
    ax2.spines['top'].set_visible(False)
    ax.annotate(f'loss {loss_hist[-1]:.3f}', xy=(steps[-1], loss_hist[-1]),
                xytext=(-104, 26), textcoords='offset points', fontsize=9.6, color=LINK,
                arrowprops=dict(arrowstyle='-|>', color=LINK, lw=1.0))
    ax2.annotate(f'{100 * acc_hist[-1]:.0f}% of held-out pairs',
                 xy=(steps[-1], 100 * acc_hist[-1]), xytext=(-176, -36),
                 textcoords='offset points', fontsize=9.6, color=SLIDE,
                 arrowprops=dict(arrowstyle='-|>', color=SLIDE, lw=1.0))
    ax.set_title('The reward model learns to agree with the pairs it was given',
                 fontsize=12.2, weight='bold')
    _save(fig, POST_DOC, 'the-reward-model-learns.svg')


def what_the_judge_can_see(w_careful: Arr, w_hurried: Arr) -> None:
    print('[p2s4] the weights the two reward models learned on what they can see:')
    for n, b, c in zip(SEEN_NAMES, w_careful, w_hurried):
        print(f'[p2s4]   {n:24s} from careful pairs {b:+.3f}   from hurried pairs {c:+.3f}')
    r_c, r_h = FEAT_R @ w_careful, FEAT_R @ w_hurried
    print(f'[p2s4] the careful reward model likes answer {int(np.argmax(r_c))} best '
          f'(true value {U_TRUE[int(np.argmax(r_c))]:.2f}), the hurried one likes answer '
          f'{int(np.argmax(r_h))} best (true value {U_TRUE[int(np.argmax(r_h))]:.2f})')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.6, 4.9), facecolor='white')
    _plain(ax)
    x = np.arange(len(SEEN_NAMES))
    ax.bar(x - 0.19, w_careful, width=0.36, color=LINK,
           label='learned from the careful pairs')
    ax.bar(x + 0.19, w_hurried, width=0.36, color=GRIP,
           label='learned from the hurried pairs')
    for i in range(len(SEEN_NAMES)):
        for off, v in [(-0.19, w_careful[i]), (0.19, w_hurried[i])]:
            ax.text(i + off, v + (0.06 if v >= 0 else -0.18), f'{v:+.2f}', ha='center',
                    fontsize=9.0)
    ax.axhline(0, color=INK, lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace(' it ', ' it\n') for n in SEEN_NAMES], fontsize=9.2)
    ax.set_ylabel('weight in the score', fontsize=10)
    ax.set_ylim(min(-0.6, w_careful.min() - 0.4), max(w_careful.max(), w_hurried.max()) + 0.7)
    ax.legend(fontsize=9.2, frameon=False, loc='upper right')
    ax.set_title('A reward model copies its annotator, liking for length included',
                 fontsize=11.2, weight='bold')
    _plain(ax2)
    ax2.scatter(U_TRUE, r_h, s=90, color=LINK, zorder=3)
    for i in range(N_CAND):
        ax2.annotate(f'{i}', xy=(U_TRUE[i], r_h[i]), xytext=(7, 5),
                     textcoords='offset points', fontsize=10)
    ax2.scatter([U_TRUE[HACK_I]], [r_h[HACK_I]], s=260, facecolor='none',
                edgecolor=GRIP, lw=2, zorder=4)
    ax2.annotate(f'answer {HACK_I}: the judge scores it highest\nand it is worth almost nothing',
                 xy=(U_TRUE[HACK_I], r_h[HACK_I]), xytext=(0.55, 0.80),
                 textcoords='axes fraction', fontsize=9.4, color=GRIP,
                 arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.1))
    ax2.set_xlabel('what the answer is really worth', fontsize=10)
    ax2.set_ylabel('score the hurried reward model gives', fontsize=10)
    ax2.grid(True, color=GRID, lw=0.5)
    ax2.set_title('The judge cannot see whether the action is right',
                  fontsize=11.2, weight='bold')
    _save(fig, POST_DOC, 'what-the-judge-can-see.svg')


def run_rl(reward: Arr, beta: float, theta0: Arr | None = None,
           pi_ref: Arr | None = None, steps: int = 250, lr: float = 0.12
           ) -> tuple[Arr, list[Arr], list[float], list[float], list[float], list[float]]:
    theta = THETA_REF.copy() if theta0 is None else theta0.copy()
    ref = PI_REF if pi_ref is None else pi_ref
    r = FEAT_R @ reward
    words = np.array([c[5] for c in CAND], dtype=float)
    pis, score, true_u, kl, length = [], [], [], [], []
    for _ in range(steps):
        pi = _softmax(theta)
        pis.append(pi.copy())
        score.append(float(pi @ r))
        true_u.append(float(pi @ U_TRUE))
        kl.append(float(np.sum(pi * np.log(pi / ref))))
        length.append(float(pi @ words))
        h = r - beta * np.log(pi / ref)
        grad = pi * (h - float(pi @ h))
        theta = theta + lr * grad
    return _softmax(theta), pis, score, true_u, kl, length


def the_policy_moves(pis: list[Arr]) -> None:
    arr = np.array(pis)
    print('[p2s4] how the seven probabilities moved while the policy was improved:')
    for i in range(N_CAND):
        print(f'[p2s4]   answer {i}: {arr[0, i]:.3f} -> {arr[-1, i]:.3f}')

    fig, ax = plt.subplots(figsize=(10.6, 5.1), facecolor='white')
    _plain(ax)
    colours = [SLIDE, PURPLE, TEAL, LINK, WRIST, GRIP, '#8c6d31']
    for i in range(N_CAND):
        ax.plot(arr[:, i], color=colours[i], lw=2.2, label=f'answer {i}')
        if arr[-1, i] > 0.1:
            ax.annotate(f'{arr[-1, i]:.2f}', xy=(len(arr) - 1, arr[-1, i]),
                        xytext=(6, -3), textcoords='offset points', fontsize=9.2,
                        color=colours[i])
    ax.annotate(f'the other six end below {max(v for i, v in enumerate(arr[-1]) if v < 0.1):.2f}',
                xy=(len(arr) - 1, 0.02), xytext=(-176, 26), textcoords='offset points',
                fontsize=9.2, color=MUTED,
                arrowprops=dict(arrowstyle='-|>', color=MUTED, lw=1.0))
    ax.set_xlabel('steps of improving the model against the reward model', fontsize=10)
    ax.set_ylabel('probability the model gives that answer', fontsize=10)
    ax.set_xlim(0, len(arr) * 1.08)
    ax.set_ylim(0, 1.0)
    ax.legend(fontsize=8.8, frameon=False, ncol=2, loc='center right')
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('Reinforcement learning moves the probabilities, one small step at a time',
                 fontsize=12.2, weight='bold')
    _save(fig, POST_DOC, 'the-policy-moves.svg')


def reward_up_and_kl_up(score: list[float], kl: list[float], true_u: list[float]) -> None:
    print(f'[p2s4] the careful reward score rose from {score[0]:.3f} to {score[-1]:.3f}, '
          f'the distance from the starting model from {kl[0]:.3f} to {kl[-1]:.3f}, '
          f'and the true value from {true_u[0]:.3f} to {true_u[-1]:.3f}')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.8), facecolor='white')
    _plain(ax)
    ax.plot(score, color=JOINT, lw=2.4, label='score the reward model gives')
    ax.plot(true_u, color=SLIDE, lw=2.4, label='what the answer is really worth')
    ax.annotate(f'{score[-1]:.2f}', xy=(len(score) - 1, score[-1]), xytext=(-44, 10),
                textcoords='offset points', fontsize=9.6, color=JOINT)
    ax.annotate(f'{true_u[-1]:.2f}', xy=(len(true_u) - 1, true_u[-1]), xytext=(-44, 10),
                textcoords='offset points', fontsize=9.6, color=SLIDE)
    ax.set_xlabel('steps of improving the model', fontsize=10)
    ax.set_ylabel('score', fontsize=10)
    ax.legend(fontsize=9.3, frameon=False, loc='lower right')
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('Both go up, because the pairs were careful', fontsize=11.4,
                 weight='bold')
    _plain(ax2)
    ax2.plot(kl, color=PURPLE, lw=2.4)
    ax2.annotate(f'{kl[-1]:.2f}', xy=(len(kl) - 1, kl[-1]), xytext=(-44, -16),
                 textcoords='offset points', fontsize=9.6, color=PURPLE)
    ax2.set_xlabel('steps of improving the model', fontsize=10)
    ax2.set_ylabel('how far the model has moved\nfrom where it started', fontsize=10)
    ax2.grid(True, axis='y', color=GRID, lw=0.5)
    ax2.set_title('And the model drifts away from the one it started as',
                  fontsize=11.4, weight='bold')
    _save(fig, POST_DOC, 'reward-up-and-kl-up.svg')


# --------------------------------------------------------------------------
# direct preference optimisation on the same pairs
# --------------------------------------------------------------------------

DPO_BETA = 0.6


def run_dpo(beta: float = DPO_BETA, steps: int = 600, lr: float = 2.0
            ) -> tuple[list[Arr], list[float], Arr]:
    theta = THETA_REF.copy()
    pis, loss_hist = [], []
    log_ref = np.log(PI_REF)
    for _ in range(steps):
        pi = _softmax(theta)
        pis.append(pi.copy())
        log_pi = np.log(pi)
        grad = np.zeros(N_CAND)
        loss = 0.0
        for a, b in TRAIN_PAIRS:
            z = beta * ((log_pi[a] - log_ref[a]) - (log_pi[b] - log_ref[b]))
            s = 1.0 / (1.0 + np.exp(-z))
            loss += -np.log(max(s, 1e-12))
            grad[a] += -(1.0 - s) * beta
            grad[b] += (1.0 - s) * beta
        theta = theta - lr * grad / len(TRAIN_PAIRS)
        loss_hist.append(loss / len(TRAIN_PAIRS))
    return pis, loss_hist, _softmax(theta)


def dpo_log_probabilities(pis: list[Arr]) -> None:
    arr = np.array(pis)
    w, l = BEST_I, HACK_I
    n_w = sum(1 for a, _ in TRAIN_PAIRS if a == w)
    n_l = sum(1 for a, _ in TRAIN_PAIRS if a == l)
    print(f'[p2s5] in the careful pairs answer {w} was preferred {n_w} times and '
          f'answer {l} {n_l} times')
    print(f'[p2s5] during direct preference optimisation answer {w} went '
          f'{arr[0, w]:.3f} -> {arr[-1, w]:.3f} and answer {l} went '
          f'{arr[0, l]:.3f} -> {arr[-1, l]:.3f}')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.4, 4.8), facecolor='white')
    _plain(ax)
    ax.plot(arr[:, w], color=SLIDE, lw=2.4, label=f'answer {w}, usually preferred')
    ax.plot(arr[:, l], color=GRIP, lw=2.4, label=f'answer {l}, usually rejected')
    ax.annotate(f'{arr[-1, w]:.3f}', xy=(len(arr) - 1, arr[-1, w]), xytext=(-62, 8),
                textcoords='offset points', fontsize=9.6, color=SLIDE)
    ax.annotate(f'{arr[-1, l]:.3f}', xy=(len(arr) - 1, arr[-1, l]), xytext=(-62, 8),
                textcoords='offset points', fontsize=9.6, color=GRIP)
    ax.set_xlabel('steps of direct preference optimisation', fontsize=10)
    ax.set_ylabel('probability the model gives that answer', fontsize=10)
    ax.legend(fontsize=9.3, frameon=False, loc='center right')
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('The preferred answer rises, the rejected one falls',
                 fontsize=11.6, weight='bold')
    _plain(ax2)
    colours = [SLIDE, PURPLE, TEAL, LINK, WRIST, GRIP, '#8c6d31']
    for i in range(N_CAND):
        ax2.plot(np.log(arr[:, i]), color=colours[i], lw=2, label=f'answer {i}')
    ax2.set_xlabel('steps of direct preference optimisation', fontsize=10)
    ax2.set_ylabel('log of the probability', fontsize=10)
    ax2.legend(fontsize=8.4, frameon=False, ncol=4, loc='lower left')
    ax2.grid(True, axis='y', color=GRID, lw=0.5)
    ax2.set_title('All seven, as the logs the method works with', fontsize=11.6,
                  weight='bold')
    _save(fig, POST_DOC, 'dpo-log-probabilities.svg')


def dpo_margin(pis: list[Arr], beta: float = DPO_BETA) -> None:
    log_ref = np.log(PI_REF)

    def margins(pi: Arr) -> Arr:
        lp = np.log(pi)
        return np.array([beta * ((lp[a] - log_ref[a]) - (lp[b] - log_ref[b]))
                         for a, b in TRAIN_PAIRS])

    before, after = margins(pis[0]), margins(pis[-1])
    print(f'[p2s5] the hidden score gap on the training pairs went from a mean of '
          f'{before.mean():.3f} to {after.mean():.3f}, and '
          f'{100 * (after > 0).mean():.1f}% of the pairs end up the right way round')

    fig, ax = plt.subplots(figsize=(10.4, 4.8), facecolor='white')
    _plain(ax)
    bins = np.linspace(min(before.min(), after.min()) - 0.1,
                       max(before.max(), after.max()) + 0.1, 28)
    ax.hist(before, bins=bins, color=MUTED, alpha=0.8, label='before training')
    ax.hist(after, bins=bins, color=SLIDE, alpha=0.8, label='after training')
    ax.axvline(0, color=GRIP, lw=1.4, ls='--')
    ax.text(bins[0] + 0.1, ax.get_ylim()[1] * 0.60,
            'pairs left of this line\nare the wrong way round', fontsize=9.4, color=GRIP)
    ax.set_xlabel('hidden score of the preferred answer minus the rejected one', fontsize=10)
    ax.set_ylabel('pairs', fontsize=10)
    ax.legend(fontsize=9.3, frameon=False, loc='upper left')
    ax.set_title(f'No reward model is ever built, but one moves all the same: '
                 f'{100 * (after > 0).mean():.0f}% of pairs end up right',
                 fontsize=11.6, weight='bold')
    _save(fig, POST_DOC, 'dpo-margin.svg')


def two_roads_same_place(pi_rl: Arr, pi_dpo: Arr) -> None:
    print('[p2s5] final probabilities: before / reward model with RL / direct')
    for i in range(N_CAND):
        print(f'[p2s5]   answer {i}: {PI_REF[i]:.3f}  {pi_rl[i]:.3f}  {pi_dpo[i]:.3f}')
    print(f'[p2s5] true value of the answers: before {float(PI_REF @ U_TRUE):.3f}, '
          f'after reinforcement learning {float(pi_rl @ U_TRUE):.3f}, '
          f'after the direct method {float(pi_dpo @ U_TRUE):.3f}')

    fig, ax = plt.subplots(figsize=(11.0, 5.0), facecolor='white')
    _plain(ax)
    x = np.arange(N_CAND)
    ax.bar(x - 0.26, PI_REF, width=0.25, color=MUTED, label='before preferences')
    ax.bar(x, pi_rl, width=0.25, color=JOINT,
           label='reward model, then reinforcement learning')
    ax.bar(x + 0.26, pi_dpo, width=0.25, color=TEAL,
           label='direct preference optimisation')
    for i in range(N_CAND):
        for off, v in [(-0.26, PI_REF[i]), (0.0, pi_rl[i]), (0.26, pi_dpo[i])]:
            ax.text(i + off, v + 0.012, f'{v:.2f}', ha='center', fontsize=8.0)
    ax.set_xticks(x)
    ax.set_xticklabels([f'answer {i}\nworth {U_TRUE[i]:.2f}' for i in range(N_CAND)],
                       fontsize=8.6)
    ax.set_ylabel('probability the model gives that answer', fontsize=10)
    ax.set_ylim(0, max(max(pi_rl), max(pi_dpo)) * 1.24)
    ax.legend(fontsize=9.2, frameon=False, loc='upper left')
    ax.set_title('Two roads from the same pairs, and they end up in much the same place',
                 fontsize=12.2, weight='bold')
    _save(fig, POST_DOC, 'two-roads-same-place.svg')


# --------------------------------------------------------------------------
# rewards a program can check, and reasoning training
# --------------------------------------------------------------------------

JOBS: list[tuple[str, bool]] = [
    ('add two numbers', True), ('solve an equation', True),
    ('pass a written unit test', True), ('compile without errors', True),
    ('match a known answer exactly', True), ('produce valid JSON', True),
    ('reach a target joint angle in simulation', True),
    ('finish inside a time limit', True), ('keep the force under a limit', True),
    ('put the cup inside the marked square', True),
    ('write a clear explanation', False), ('be polite but firm', False),
    ('summarise a report well', False), ('choose a safe plan in a new room', False),
    ('place the cup where the person meant', False),
    ('grasp a soft fruit without bruising it', False),
    ('tidy the bench the way the owner likes', False),
    ('decide when to stop and ask', False), ('explain a failure usefully', False),
    ('hand a tool over comfortably', False),
]


def who_can_check_it() -> None:
    n_yes = sum(1 for _, y in JOBS if y)
    print(f'[p2s6] of the {len(JOBS)} jobs listed in the script, {n_yes} can be checked '
          f'by a program and {len(JOBS) - n_yes} cannot')

    fig, ax = plt.subplots(figsize=(11.6, 5.4), facecolor='white')
    _blank(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 11.6)
    yes = [j for j, y in JOBS if y]
    no = [j for j, y in JOBS if not y]
    ax.text(0.02, 10.9, f'a program can say right or wrong  ({len(yes)} jobs)',
            fontsize=10.6, weight='bold', color=SLIDE)
    ax.text(0.52, 10.9, f'only a person can say  ({len(no)} jobs)', fontsize=10.6,
            weight='bold', color=GRIP)
    for i, j in enumerate(yes):
        _box(ax, 0.02, 9.5 - i, 0.455, 0.70, j, face='#dff0e2', edge=SLIDE, size=9.2)
    for i, j in enumerate(no):
        _box(ax, 0.52, 9.5 - i, 0.455, 0.70, j, face='#fbe3e3', edge=GRIP, size=9.2)
    ax.set_title('Twenty jobs, sorted by whether a program can mark the answer',
                 fontsize=12.2, weight='bold', loc='left')
    _save(fig, POST_DOC, 'who-can-check-it.svg')


def the_verifier_trains_it() -> None:
    rng = np.random.default_rng(606)
    n_prob, n_cand = 30, 8
    theta = rng.normal(0, 0.7, size=(n_prob, n_cand))
    right = rng.integers(0, n_cand, size=n_prob)
    hist: list[float] = []
    for _ in range(140):
        pass_rate = 0.0
        grad = np.zeros_like(theta)
        for i in range(n_prob):
            pi = _softmax(theta[i])
            pass_rate += pi[right[i]]
            base = float(pi[right[i]])
            for _ in range(6):
                a = int(rng.choice(n_cand, p=pi))
                r = 1.0 if a == right[i] else 0.0
                onehot = np.zeros(n_cand)
                onehot[a] = 1.0
                grad[i] += (r - base) * (onehot - pi) / 6.0
        hist.append(pass_rate / n_prob)
        theta += 1.6 * grad
    print(f'[p2s6] training against the checker lifted the pass rate from '
          f'{100 * hist[0]:.1f}% to {100 * hist[-1]:.1f}% on {n_prob} problems, '
          f'with no human and no reward model')

    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plain(ax)
    ax.plot([100 * h for h in hist], color=SLIDE, lw=2.4)
    ax.annotate(f'{100 * hist[0]:.0f}% at the start', xy=(0, 100 * hist[0]),
                xytext=(20, 26), textcoords='offset points', fontsize=9.6,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0))
    ax.annotate(f'{100 * hist[-1]:.0f}% after {len(hist)} steps',
                xy=(len(hist) - 1, 100 * hist[-1]), xytext=(-180, -34),
                textcoords='offset points', fontsize=9.6,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0))
    ax.set_xlabel('steps of training against the checker', fontsize=10)
    ax.set_ylabel('chance of giving the right answer, %', fontsize=10)
    ax.set_ylim(0, 105)
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('A checking program is enough to train on: 30 problems, 8 candidate answers each',
                 fontsize=12.0, weight='bold')
    _save(fig, POST_DOC, 'the-verifier-trains-it.svg')


def pass_at_k() -> None:
    ks = np.arange(1, 33)
    ps = [0.12, 0.30, 0.60]
    print('[p2s6] chance that at least one of k tries is right:')
    for p in ps:
        vals = 1 - (1 - p) ** ks
        need = int(np.ceil(np.log(0.05) / np.log(1 - p)))
        print(f'[p2s6]   one try {p:.2f} -> 8 tries {vals[7]:.3f}, '
              f'32 tries {vals[31]:.3f}, {need} tries for 95%')

    fig, ax = plt.subplots(figsize=(10.2, 4.8), facecolor='white')
    _plain(ax)
    for p, colour in zip(ps, [GRIP, JOINT, SLIDE]):
        vals = 1 - (1 - p) ** ks
        ax.plot(ks, 100 * vals, color=colour, lw=2.2,
                label=f'right {100 * p:.0f}% of the time on one try')
        if p == ps[0]:
            for k in (8, 32):
                ax.annotate(f'{100 * vals[k - 1]:.0f}% after {k} tries',
                            xy=(k, 100 * vals[k - 1]), xytext=(-10, -24),
                            textcoords='offset points', fontsize=9.4, color=colour,
                            arrowprops=dict(arrowstyle='-|>', color=colour, lw=1.0))
    ax.set_xlabel('tries at the same problem', fontsize=10)
    ax.set_ylabel('chance at least one try passes the checker, %', fontsize=10)
    ax.set_ylim(0, 108)
    ax.legend(fontsize=9.3, frameon=False, loc='lower right')
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('Why trying many times works: the checker only has to find one right answer',
                 fontsize=12.0, weight='bold')
    _save(fig, POST_DOC, 'pass-at-k.svg')


def working_out_tokens() -> None:
    q, n_steps, per_step, drift, leap = 0.93, 6, 18, 0.0004, 3.0
    ts = np.arange(0, 401, 4)
    acc = np.array([q ** (min(n_steps, int(t // per_step))
                          + leap * (n_steps - min(n_steps, int(t // per_step))))
                    * (1 - drift) ** t for t in ts])
    best = int(np.argmax(acc))
    at_108 = float(acc[list(ts).index(108)])
    print(f'[p2s6] illustrative working-out curve: 0 tokens {acc[0]:.3f}, '
          f'{per_step * n_steps} tokens {at_108:.3f}, best {acc[best]:.3f} at '
          f'{ts[best]} tokens, 400 tokens {acc[-1]:.3f}')
    print(f'[p2s6] {ts[best]} working-out tokens cost {ts[best] / DECODE_RATE:.1f} s at '
          f'{DECODE_RATE:.0f} tokens a second, and 400 cost {400 / DECODE_RATE:.1f} s')

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(ts, 100 * acc, color=LINK, lw=2.4)
    ax.axvline(ts[best], color=SLIDE, lw=1.3, ls='--')
    ax.annotate(f'best {100 * acc[best]:.0f}% at {ts[best]} tokens',
                xy=(ts[best], 100 * acc[best]), xytext=(30, -18),
                textcoords='offset points', fontsize=9.8, color=SLIDE,
                arrowprops=dict(arrowstyle='-|>', color=SLIDE, lw=1.0))
    ax.annotate(f'answering straight away: {100 * acc[0]:.0f}%', xy=(0, 100 * acc[0]),
                xytext=(30, 30), textcoords='offset points', fontsize=9.8, color=GRIP,
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.0))
    ax.set_xlabel('tokens of working-out written before the answer', fontsize=10)
    ax.set_ylabel('problems answered right, % (illustrative)', fontsize=10)
    ax.set_ylim(0, 80)
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ticks = np.array([0, 100, 200, 300, 400])
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f'{t / DECODE_RATE:.1f} s' for t in ticks], fontsize=9.3,
                        color=WRIST)
    ax2.set_xlabel(f'time that working-out takes to write, at {DECODE_RATE:.0f} tokens a second',
                   fontsize=9.8, color=WRIST)
    ax.set_title('Illustrative: working-out tokens buy accuracy, then stop buying it',
                 fontsize=12.2, weight='bold', pad=36)
    _save(fig, POST_DOC, 'working-out-tokens.svg')


# --------------------------------------------------------------------------
# reward hacking
# --------------------------------------------------------------------------

def pleasing_the_judge(score: list[float], true_u: list[float]) -> None:
    best = int(np.argmax(true_u))
    print(f'[p2s7] against the hurried reward model the score rose from {score[0]:.3f} '
          f'to {score[-1]:.3f}, while the true value peaked at {true_u[best]:.3f} on '
          f'step {best} and fell to {true_u[-1]:.3f}')

    fig, ax = plt.subplots(figsize=(10.6, 5.0), facecolor='white')
    _plain(ax)
    ax.plot(score, color=JOINT, lw=2.4, label='score the reward model gives')
    ax.plot(true_u, color=GRIP, lw=2.4, label='what the answer is really worth')
    ax.axvline(best, color=SLIDE, lw=1.3, ls='--')
    ax.annotate(f'best real answers,\nstep {best}', xy=(best, true_u[best]),
                xytext=(46, -56), textcoords='offset points', fontsize=9.6, color=SLIDE,
                arrowprops=dict(arrowstyle='-|>', color=SLIDE, lw=1.0))
    ax.annotate(f'score {score[-1]:.2f}', xy=(len(score) - 1, score[-1]),
                xytext=(-104, 10), textcoords='offset points', fontsize=9.6, color=JOINT)
    ax.annotate(f'real worth {true_u[-1]:.2f}', xy=(len(true_u) - 1, true_u[-1]),
                xytext=(-128, 14), textcoords='offset points', fontsize=9.6, color=GRIP)
    ax.set_xlabel('steps of improving the model against the hurried reward model',
                  fontsize=10)
    ax.set_ylabel('score', fontsize=10)
    ax.legend(fontsize=9.4, frameon=False, loc='center right')
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('Reward hacking: the number being chased goes up while the answers get worse',
                 fontsize=12.2, weight='bold')
    _save(fig, POST_DOC, 'pleasing-the-judge.svg')


def answers_get_longer(length: list[float], pis: list[Arr]) -> None:
    arr = np.array(pis)
    print(f'[p2s7] the average answer grew from {length[0]:.1f} words to '
          f'{length[-1]:.1f} words; answer {HACK_I} went from {arr[0, HACK_I]:.3f} to '
          f'{arr[-1, HACK_I]:.3f} and answer {BEST_I} from {arr[0, BEST_I]:.3f} to '
          f'{arr[-1, BEST_I]:.3f}')

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.7), facecolor='white')
    _plain(ax)
    ax.plot(length, color=PURPLE, lw=2.4)
    ax.set_ylim(min(length) - 3, max(length) + 5)
    ax.annotate(f'{length[0]:.1f} words', xy=(0, length[0]), xytext=(34, 16),
                textcoords='offset points', fontsize=9.6,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0))
    ax.annotate(f'{length[-1]:.1f} words', xy=(len(length) - 1, length[-1]),
                xytext=(-130, -28), textcoords='offset points', fontsize=9.6,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0))
    ax.set_xlabel('steps against the hurried reward model', fontsize=10)
    ax.set_ylabel('average length of the answer, words', fontsize=10)
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('The answers get longer because length scores well',
                 fontsize=11.4, weight='bold')
    _plain(ax2)
    ax2.plot(arr[:, HACK_I], color=GRIP, lw=2.4,
             label=f'answer {HACK_I}: longest, worth {U_TRUE[HACK_I]:.2f}')
    ax2.plot(arr[:, BEST_I], color=SLIDE, lw=2.4,
             label=f'answer {BEST_I}: best, worth {U_TRUE[BEST_I]:.2f}')
    ax2.set_xlabel('steps against the hurried reward model', fontsize=10)
    ax2.set_ylabel('probability the model gives that answer', fontsize=10)
    ax2.set_ylim(0, 1.05)
    ax2.legend(fontsize=9.3, frameon=False, loc='center right')
    ax2.grid(True, axis='y', color=GRID, lw=0.5)
    ax2.set_title('The answer that wins is the one that games the score',
                  fontsize=11.4, weight='bold')
    _save(fig, POST_DOC, 'answers-get-longer.svg')


def the_brake(reward: Arr, theta0: Arr, pi_good: Arr) -> None:
    betas = [0.0, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6]
    finals_true, finals_score = [], []
    for b in betas:
        _, _, score, true_u, kl, _ = run_rl(reward, b, theta0, pi_good, steps=1200)
        finals_true.append(true_u[-1])
        finals_score.append(score[-1])
        print(f'[p2s7] brake {b:.2f}: reward score {score[-1]:.3f}, '
              f'true value {true_u[-1]:.3f}, distance moved {kl[-1]:.3f}')
    best = int(np.argmax(finals_true))

    fig, ax = plt.subplots(figsize=(10.4, 5.0), facecolor='white')
    _plain(ax)
    x = np.arange(len(betas))
    ax.plot(x, finals_score, marker='o', color=JOINT, lw=2.2,
            label='score the hurried reward model gives')
    ax.plot(x, finals_true, marker='s', color=GRIP, lw=2.2,
            label='what the answer is really worth')
    ax.axvline(best, color=SLIDE, lw=1.3, ls='--')
    ax.annotate(f'best real answers at a brake of {betas[best]}',
                xy=(best, finals_true[best]), xytext=(-176, -92),
                textcoords='offset points', fontsize=9.6, color=SLIDE,
                arrowprops=dict(arrowstyle='-|>', color=SLIDE, lw=1.0))
    ax.set_xticks(x)
    ax.set_xticklabels([f'{b}' for b in betas], fontsize=9.6)
    ax.set_xlabel('how hard the model is held near the one it started as', fontsize=10)
    ax.set_ylabel('score at the end of training', fontsize=10)
    ax.legend(fontsize=9.4, frameon=False, loc='center left')
    ax.grid(True, axis='y', color=GRID, lw=0.5)
    ax.set_title('The brake that slows the hack: hold the model near where it started',
                 fontsize=12.2, weight='bold')
    _save(fig, POST_DOC, 'the-brake.svg')


# --------------------------------------------------------------------------
def page_two() -> None:
    base = LM(CORP.vocab + ['<s>', '</s>', '<unk>', ROLE_U, ROLE_A, '<|end|>'])
    for s in CORP.sentences:
        base.add_sentence(s)
    before_ans, before_q = _mean_reply_mass(base)
    before_drawers = _drawer_right(base)
    a_question_gets_another_question(base)

    sizes = [0, 2, 8, 32, 128, 512]
    golds, masses = [], []
    added, demo_words = 0, 0
    for n in sizes:
        while added < n:
            q, a = DEMOS[added % len(DEMOS)]
            line = f'{ROLE_U} {q} {ROLE_A} {a} <|end|>'
            base.add_sentence(line.split())
            demo_words += len(line.split())
            added += 1
        golds.append(base.p(f'{ROLE_U} {GOLD_Q} {ROLE_A}'.split(), GOLD_A.split()[0]))
        masses.append(_mean_reply_mass(base)[0])
        print(f'[p2s2] {n:4d} demonstrations -> p(start of the right answer) '
              f'{golds[-1]:.3f}, p(reply starts an answer) {masses[-1]:.3f}')
    after_ans, after_q = _mean_reply_mass(base)
    after_drawers = _drawer_right(base)

    after_instruction_tuning(base)
    pair_words = sum(len(CAND[a][0].split()) + len(CAND[b][0].split()) + 15
                     for a, b in TRAIN_PAIRS)
    three_stages(demo_words, pair_words)
    one_demonstration()
    demonstrations_and_the_answer(sizes, golds, masses)
    what_tuning_does_not_fix((before_ans, before_q, before_drawers),
                             (after_ans, after_q, after_drawers))

    seven_answers_and_their_qualities()
    a_preference_pair()
    where_the_pairs_disagree()

    reward, loss_hist, acc_hist = fit_reward_model(TRAIN_PAIRS, TEST_PAIRS)
    bad_reward, _, bad_acc = fit_reward_model(HURRIED_TRAIN, HURRIED_TEST)
    the_reward_model_learns(loss_hist, acc_hist)
    what_the_judge_can_see(reward, bad_reward)
    pi_rl, pis_rl, score, true_u, kl, length = run_rl(reward, 0.30)
    the_policy_moves(pis_rl)
    reward_up_and_kl_up(score, kl, true_u)

    pis_dpo, dpo_loss, pi_dpo = run_dpo()
    print(f'[p2s5] the direct method drove its loss from {dpo_loss[0]:.3f} to '
          f'{dpo_loss[-1]:.3f}')
    dpo_log_probabilities(pis_dpo)
    dpo_margin(pis_dpo)
    two_roads_same_place(pi_rl, pi_dpo)

    who_can_check_it()
    the_verifier_trains_it()
    pass_at_k()
    working_out_tokens()

    theta_good = np.log(pi_dpo)
    _, pis_hack, score_h, true_h, _, length_h = run_rl(bad_reward, 0.0, theta_good,
                                                       pi_dpo, steps=1200)
    pleasing_the_judge(score_h, true_h)
    answers_get_longer(length_h, pis_hack)
    the_brake(bad_reward, theta_good, pi_dpo)


if __name__ == '__main__':
    main()
