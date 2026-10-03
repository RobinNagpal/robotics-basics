"""Generate the diagrams for docs/06_neural-networks/05_turning-the-world-into-numbers/.

    01_tokens-and-embeddings.md            -> images/turning-the-world-into-numbers/tokens-and-embeddings/
    02_pictures-sound-and-robot-states.md  -> images/turning-the-world-into-numbers/pictures-sound-and-robot-states/

Run with:  python3 docs/diagrams/turning_the_world_into_numbers.py
Add --png <folder> to also write PNG copies for checking by eye.

Every number drawn in a picture is worked out in this file, and the script
prints the numbers so that the two documents can quote the same values.

What is simulated, and what is real arithmetic on top of it:

* The text is simulated. A corpus of robot instructions is built from sentence
  templates with numpy.random.default_rng(11), and the byte pair encoding
  tokeniser, its merge list, its vocabulary and every token count printed here
  are the real output of running that algorithm on that corpus. A large model's
  tokeniser is trained the same way on far more text, so it splits words a
  little differently.
* The embedding table is simulated in the same sense. It is a real positive
  pointwise mutual information matrix counted from that corpus and reduced by a
  real singular value decomposition, so the cosine similarities are real
  arithmetic on real counts, but the counts come from made-up sentences.
* The pictures, the depth frame, the point cloud, the sound and the arm
  readings are simulated with numpy.random.default_rng seeds given in each
  function. The projections, the short-time Fourier transform, the forward
  kinematics, the losses and the small training runs on top of them are real
  NumPy arithmetic.
"""

import pathlib
import sys
from collections import Counter

import matplotlib
matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrow, FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

IMAGES: pathlib.Path = (pathlib.Path(__file__).resolve().parents[1] / 'images'
                        / 'turning-the-world-into-numbers')
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

TOK_DOC: str = 'tokens-and-embeddings'
STA_DOC: str = 'pictures-sound-and-robot-states'

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


def _arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float,
           colour: str = INK, lw: float = 1.3) -> None:
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='-|>', color=colour, lw=lw,
                                shrinkA=0, shrinkB=0))


def _grid_of_numbers(ax: Axes, values: Arr, fmt: str = '{:.0f}',
                     cell: float = 1.0, cmap: str = 'Greys', vmin: float | None = None,
                     vmax: float | None = None, size: float = 8.0,
                     flip: bool = True) -> None:
    """Draw a 2D array as a shaded grid with the number written in each cell."""
    rows, cols = values.shape
    lo = float(np.nanmin(values)) if vmin is None else vmin
    hi = float(np.nanmax(values)) if vmax is None else vmax
    cm = plt.get_cmap(cmap)
    for r in range(rows):
        for c in range(cols):
            v = values[r, c]
            yy = (rows - 1 - r) if flip else r
            if np.isnan(v):
                ax.add_patch(Rectangle((c * cell, yy * cell), cell, cell,
                                       facecolor='#f2c3c3', edgecolor='white', lw=0.8))
                ax.text((c + 0.5) * cell, (yy + 0.5) * cell, '--', ha='center',
                        va='center', fontsize=size, color=GRIP)
                continue
            t = 0.5 if hi == lo else (v - lo) / (hi - lo)
            ax.add_patch(Rectangle((c * cell, yy * cell), cell, cell,
                                   facecolor=cm(0.12 + 0.75 * t), edgecolor='white',
                                   lw=0.8))
            ax.text((c + 0.5) * cell, (yy + 0.5) * cell, fmt.format(v), ha='center',
                    va='center', fontsize=size,
                    color='white' if t > 0.62 else INK)
    ax.set_xlim(-0.05 * cell, cols * cell + 0.05 * cell)
    ax.set_ylim(-0.05 * cell, rows * cell + 0.05 * cell)
    ax.set_aspect('equal')
    _blank(ax)


# --------------------------------------------------------------------------
# the simulated corpus of robot instructions
# --------------------------------------------------------------------------

VERBS: list[str] = [
    'pick up', 'put down', 'place', 'move', 'grasp', 'release', 'push', 'pull',
    'rotate', 'lift', 'lower', 'open', 'close', 'hold', 'carry', 'slide', 'stack',
    'insert', 'align', 'inspect', 'wipe', 'pour', 'fold', 'press', 'tighten',
    'loosen', 'unplug', 'plug', 'sort', 'weigh', 'measure', 'scan', 'photograph',
    'dispense', 'assemble', 'disassemble', 'calibrate', 'recalibrate', 'retract',
    'approach', 'withdraw', 'reposition', 'realign', 'regrasp', 'reorient',
    'straighten', 'untangle', 'unscrew', 'rethread', 'deburr']
OBJECTS: list[str] = [
    'mug', 'cup', 'bowl', 'plate', 'block', 'box', 'bottle', 'can', 'jar', 'screw',
    'bolt', 'nut', 'tray', 'lid', 'spoon', 'tool', 'cloth', 'sponge', 'handle',
    'cube', 'washer', 'bracket', 'bearing', 'spanner', 'spacer', 'gasket',
    'connector', 'cartridge', 'canister', 'container', 'cylinder', 'flange',
    'fastener', 'grommet', 'sprocket', 'terminal', 'thermometer', 'calliper',
    'micrometer', 'dispenser', 'decanter', 'funnel', 'pipette', 'beaker',
    'stopper', 'clamp', 'wrench', 'ratchet', 'tweezers', 'syringe']
COLOURS: list[str] = ['red', 'blue', 'green', 'yellow', 'white', 'black', 'grey',
                      'orange', 'purple', 'brown', 'transparent', 'reflective',
                      'matte', 'glossy', 'speckled', 'striped']
MATERIALS: list[str] = ['metal', 'plastic', 'glass', 'rubber', 'steel', 'aluminium',
                        'ceramic', 'cardboard', 'silicone', 'stainless', 'brass',
                        'titanium', 'wooden', 'foam', 'fabric', 'laminated']
PLACES: list[str] = ['table', 'shelf', 'tray', 'bin', 'sink', 'rack', 'workbench',
                     'conveyor', 'drawer', 'pallet', 'cupboard', 'turntable',
                     'fixture', 'cradle', 'carousel', 'dishwasher', 'countertop',
                     'platform', 'enclosure', 'receptacle']
PARTS: list[str] = ['gripper', 'wrist', 'elbow', 'camera', 'arm', 'base', 'finger',
                    'shoulder', 'forearm', 'fingertip', 'wristband', 'encoder',
                    'actuator', 'manipulator', 'end-effector', 'rangefinder']
EXTRA: list[str] = ['slowly', 'carefully', 'gently', 'again', 'twice', 'now',
                    'firmly', 'smoothly', 'steadily', 'repeatedly', 'immediately',
                    'horizontally', 'vertically', 'diagonally', 'symmetrically',
                    'deliberately']


def _zipf(items: list[str], rng: np.random.Generator, n: int) -> list[str]:
    """Draw n items with a Zipf-like weighting, so the end of the list stays rare."""
    w = 1.0 / (1.0 + np.arange(len(items))) ** 1.15
    w = w / w.sum()
    idx = rng.choice(len(items), size=n, p=w)
    return [items[i] for i in idx]


def _corpus() -> list[str]:
    """Build the simulated corpus of robot instructions. Seeded, so it never changes."""
    rng = np.random.default_rng(11)
    n = 3200
    vs = _zipf(VERBS, rng, n * 2)
    os_ = _zipf(OBJECTS, rng, n * 2)
    cs = _zipf(COLOURS, rng, n)
    ms = _zipf(MATERIALS, rng, n)
    ps = _zipf(PLACES, rng, n)
    pts = _zipf(PARTS, rng, n)
    xs = _zipf(EXTRA, rng, n)
    out: list[str] = []
    for i in range(n):
        shape = int(rng.integers(0, 8))
        v, v2 = vs[i], vs[n + i]
        o, o2 = os_[i], os_[n + i]
        c, m, p, part, ex = cs[i], ms[i], ps[i], pts[i], xs[i]
        if shape == 0:
            out.append(f'{v} the {c} {o} and put it on the {p}')
        elif shape == 1:
            out.append(f'{v} the {m} {o} into the {o2} on the {p}')
        elif shape == 2:
            out.append(f'move the {part} to the {p} {ex}')
        elif shape == 3:
            out.append(f'{v} the {o} {ex} and then {v2} the {c} {o2}')
        elif shape == 4:
            out.append(f'close the {part} on the {o} and lift it off the {p}')
        elif shape == 5:
            out.append(f'the {c} {o} is on the {p} next to the {m} {o2}')
        elif shape == 6:
            out.append(f'{v} the {o} that is nearest to the {part}')
        else:
            out.append(f'if the {o} is in the {p} then {v} the {o} {ex}')
    return out


# --------------------------------------------------------------------------
# byte pair encoding, trained on that corpus
# --------------------------------------------------------------------------

END: str = '_'      # stands for the space in front of a word, as in '_mug'


def _word_counts(corpus: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in corpus:
        for w in line.split():
            counts[END + w] += 1
    return counts


def _train_bpe(counts: Counter[str], n_merges: int) -> tuple[list[tuple[str, str]],
                                                             list[int]]:
    """Return the merge list in the order it was found, and the count behind each merge."""
    pieces: dict[str, list[str]] = {w: list(w) for w in counts}
    merges: list[tuple[str, str]] = []
    strengths: list[int] = []
    for _ in range(n_merges):
        pair_counts: Counter[tuple[str, str]] = Counter()
        for w, n in counts.items():
            ps = pieces[w]
            for a, b in zip(ps, ps[1:]):
                pair_counts[(a, b)] += n
        if not pair_counts:
            break
        (a, b), n = pair_counts.most_common(1)[0]
        if n < 2:
            break
        merges.append((a, b))
        strengths.append(n)
        joined = a + b
        for w in pieces:
            ps = pieces[w]
            if len(ps) < 2:
                continue
            new: list[str] = []
            i = 0
            while i < len(ps):
                if i + 1 < len(ps) and ps[i] == a and ps[i + 1] == b:
                    new.append(joined)
                    i += 2
                else:
                    new.append(ps[i])
                    i += 1
            pieces[w] = new
    return merges, strengths


class Tok:
    """A real byte pair encoding tokeniser trained on the simulated corpus."""

    def __init__(self, n_merges: int = 400) -> None:
        self.corpus: list[str] = _corpus()
        self.counts: Counter[str] = _word_counts(self.corpus)
        self.merges, self.strengths = _train_bpe(self.counts, n_merges)
        self.rank: dict[tuple[str, str], int] = {m: i for i, m in enumerate(self.merges)}
        alphabet = sorted({ch for w in self.counts for ch in w})
        vocab: list[str] = ['<pad>', '<unk>'] + alphabet
        for a, b in self.merges:
            if a + b not in vocab:
                vocab.append(a + b)
        self.vocab: list[str] = vocab
        self.ids: dict[str, int] = {t: i for i, t in enumerate(vocab)}
        self.cache: dict[str, list[str]] = {}

    def split_word(self, word: str) -> list[str]:
        if word in self.cache:
            return self.cache[word]
        ps: list[str] = list(word)
        while len(ps) > 1:
            best: tuple[int, int] | None = None
            for i, (a, b) in enumerate(zip(ps, ps[1:])):
                r = self.rank.get((a, b))
                if r is not None and (best is None or r < best[0]):
                    best = (r, i)
            if best is None:
                break
            i = best[1]
            ps = ps[:i] + [ps[i] + ps[i + 1]] + ps[i + 2:]
        self.cache[word] = ps
        return ps

    def split(self, text: str) -> list[str]:
        out: list[str] = []
        for w in text.split():
            out.extend(self.split_word(END + w))
        return out

    def encode(self, text: str) -> list[int]:
        return [self.ids.get(p, 1) for p in self.split(text)]


TOKENISER: Tok | None = None


def _tok() -> Tok:
    global TOKENISER
    if TOKENISER is None:
        TOKENISER = Tok()
    return TOKENISER


# --------------------------------------------------------------------------
# the embedding table: counted from the corpus, reduced by a singular value
# decomposition
# --------------------------------------------------------------------------

SHOW_WORDS: list[str] = ['mug', 'cup', 'bowl', 'block', 'cube', 'screw', 'bolt',
                         'table', 'shelf', 'bin', 'gripper', 'wrist', 'camera',
                         'red', 'blue', 'green', 'pick', 'place', 'lift', 'push',
                         'rotate', 'close', 'open', 'slowly', 'carefully', 'the',
                         'it', 'on', 'into', 'and']


class Emb:
    """Real word vectors counted from the simulated corpus."""

    def __init__(self, dim: int = 64, window: int = 3) -> None:
        corpus = _tok().corpus
        freq: Counter[str] = Counter()
        for line in corpus:
            freq.update(line.split())
        self.words: list[str] = [w for w, _ in freq.most_common(60)]
        for w in SHOW_WORDS:
            if w not in self.words and w in freq:
                self.words.append(w)
        self.index: dict[str, int] = {w: i for i, w in enumerate(self.words)}
        self.freq: Counter[str] = freq
        n = len(self.words)
        co = np.zeros((n, n))
        for line in corpus:
            ws = [w for w in line.split()]
            for i, w in enumerate(ws):
                if w not in self.index:
                    continue
                for j in range(max(0, i - window), min(len(ws), i + window + 1)):
                    if j == i or ws[j] not in self.index:
                        continue
                    co[self.index[w], self.index[ws[j]]] += 1.0
        total = co.sum()
        pw = co.sum(axis=1) / total
        pc = co.sum(axis=0) / total
        with np.errstate(divide='ignore', invalid='ignore'):
            pmi = np.log((co / total) / np.outer(pw, pc))
        ppmi = np.nan_to_num(np.maximum(pmi, 0.0), nan=0.0, posinf=0.0, neginf=0.0)
        u, s, _ = np.linalg.svd(ppmi, full_matrices=False)
        k = min(dim, u.shape[1])
        self.full: Arr = u[:, :k] * s[:k]
        self.scale: float = float(np.abs(self.full).max())
        self.full = self.full / self.scale
        self.small: Arr = np.round(self.full[:, :6], 2)

    def vec(self, word: str, dims: int = 6) -> Arr:
        return self.small[self.index[word]] if dims == 6 else self.full[self.index[word]]


EMB: Emb | None = None


def _emb() -> Emb:
    global EMB
    if EMB is None:
        EMB = Emb()
    return EMB


def _cos(a: Arr, b: Arr) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def report_text_machinery() -> None:
    """Print the facts about the corpus and the tokeniser that the page quotes."""
    t = _tok()
    words = sum(t.counts.values())
    print(f'[corpus] {len(t.corpus)} sentences, {words} words, '
          f'{len(t.counts)} different words, {len(t.vocab)} tokens in the vocabulary')
    print(f'[bpe] {len(t.merges)} merges; first 12: '
          + ', '.join(f'{a}+{b}={a + b} ({n})'
                      for (a, b), n in zip(t.merges[:12], t.strengths[:12])))
    e = _emb()
    print(f'[emb] {len(e.words)} words in the table, {e.full.shape[1]} numbers each, '
          f'first 6 kept for drawing')


SENTENCES: list[str] = [
    'pick up the blue mug and put it on the tray',
    'move the gripper to the shelf above the workbench',
    'unscrew the polycarbonate lid and place it in the bin',
    'close the gripper until the force sensor reads two newtons',
    'stack the three red blocks on the left side of the table',
]


def _piece_row(ax: Axes, pieces: list[str], ids: list[int], y: float,
               face: str = LINK_PALE, char_w: float = 0.30, gap: float = 0.08,
               size: float = 10.0, x0: float = 0.0, show_ids: bool = True,
               height: float = 0.62) -> float:
    """Draw one row of token boxes, each box as wide as its text, ids underneath."""
    x = x0
    for p, i in zip(pieces, ids):
        w = max(0.52, char_w * len(p) + 0.18)
        _box(ax, x, y, w, height, p.replace(END, '␣'), face=face, size=size,
             family='DejaVu Sans Mono')
        if show_ids:
            ax.text(x + w / 2, y - 0.19, str(i), ha='center', va='center', fontsize=7.8,
                    color=MUTED)
        x += w + gap
    return x


# --------------------------------------------------------------------------
# 01_tokens-and-embeddings, section 1: what a token is
# --------------------------------------------------------------------------

def sentence_into_tokens() -> None:
    t = _tok()
    s = SENTENCES[0]
    pieces = t.split(s)
    ids = t.encode(s)
    print(f'[s1] "{s}": {len(s.split())} words, {len(pieces)} tokens, '
          f'{len(s.replace(" ", ""))} letters')
    print(f'[s1] pieces {pieces}')
    print(f'[s1] ids {ids}')

    fig, ax = plt.subplots(figsize=(11.4, 3.5), facecolor='white')
    _blank(ax)
    ax.text(0.0, 2.45, 'the sentence as it is typed', fontsize=10, color=MUTED)
    ax.text(0.0, 2.05, s, fontsize=13, color=INK, family='DejaVu Sans Mono')
    ax.text(0.0, 1.35, 'cut into tokens  (␣ marks the space in front of a word)',
            fontsize=10, color=MUTED)
    end = _piece_row(ax, pieces, ids, 0.55)
    ax.text(0.0, 0.02, 'the number under each box is that token’s place in the '
                       f'vocabulary of {len(t.vocab)} tokens', fontsize=9.5, color=MUTED)
    ax.set_xlim(-0.2, max(end, 11.0) + 0.2)
    ax.set_ylim(-0.15, 3.0)
    ax.set_title(f'{len(s.split())} words become {len(pieces)} tokens, and the model '
                 f'only ever sees the {len(ids)} numbers',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'sentence-into-tokens.svg')


def common_and_rare() -> None:
    t = _tok()
    words = ['mug', 'gripper', 'thermometer', 'recalibrate', 'polycarbonate']
    rows = []
    for w in words:
        key = END + w
        pieces = t.split_word(key)
        rows.append((w, t.counts.get(key, 0), pieces, [t.ids.get(p, 1) for p in pieces]))
        print(f'[s1] "{w}" seen {t.counts.get(key, 0)} times -> {len(pieces)} tokens '
              f'{pieces}')

    fig, ax = plt.subplots(figsize=(11.6, 4.4), facecolor='white')
    _blank(ax)
    ax.text(0.0, len(rows) * 1.05 + 0.5, 'word', fontsize=10, color=MUTED, weight='bold')
    ax.text(2.6, len(rows) * 1.05 + 0.5, 'times in the training text', fontsize=10,
            color=MUTED, weight='bold')
    ax.text(6.4, len(rows) * 1.05 + 0.5, 'the tokens it becomes', fontsize=10,
            color=MUTED, weight='bold')
    for k, (w, n, pieces, ids) in enumerate(rows):
        y = (len(rows) - 1 - k) * 1.05
        ax.text(0.0, y + 0.31, w, fontsize=11.5, color=INK, family='DejaVu Sans Mono')
        ax.text(3.2, y + 0.31, f'{n:,}' if n else 'never', fontsize=11,
                color=INK if n else GRIP, ha='center')
        face = LINK_PALE if len(pieces) == 1 else '#f6ddc8'
        _piece_row(ax, pieces, ids, y, face=face, x0=6.4, size=9.5, height=0.60)
        ax.text(14.6, y + 0.31, f'{len(pieces)} token' + ('' if len(pieces) == 1 else 's'),
                fontsize=10, color=MUTED, ha='right')
    ax.set_xlim(-0.2, 15.0)
    ax.set_ylim(-0.35, len(rows) * 1.05 + 0.95)
    ax.set_title('A common word is one token; a rare word is spelled out of several, '
                 'and a word never seen is still spellable',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'common-and-rare.svg')


def token_counts() -> None:
    t = _tok()
    words = [len(s.split()) for s in SENTENCES]
    toks = [len(t.split(s)) for s in SENTENCES]
    letters = [len(s.replace(' ', '')) for s in SENTENCES]
    for i, s in enumerate(SENTENCES):
        print(f'[s1] sentence {i + 1}: {words[i]} words, {toks[i]} tokens, '
              f'{letters[i]} letters -> {toks[i] / words[i]:.2f} tokens per word')
    print(f'[s1] totals: {sum(words)} words, {sum(toks)} tokens, {sum(letters)} letters, '
          f'{sum(toks) / sum(words):.2f} tokens per word')

    fig, ax = plt.subplots(figsize=(11.6, 5.2), facecolor='white')
    _plain(ax)
    y = np.arange(len(SENTENCES))
    h = 0.26
    ax.barh(y + h, letters, height=h, color=MUTED, label='single letters')
    ax.barh(y, toks, height=h, color=LINK, label='subword tokens')
    ax.barh(y - h, words, height=h, color=SLIDE, label='whole words')
    for i in range(len(SENTENCES)):
        ax.text(letters[i] + 0.6, y[i] + h, str(letters[i]), va='center', fontsize=9,
                color=MUTED)
        ax.text(toks[i] + 0.6, y[i], str(toks[i]), va='center', fontsize=9, color=LINK,
                weight='bold')
        ax.text(words[i] + 0.6, y[i] - h, str(words[i]), va='center', fontsize=9,
                color=SLIDE)
    ax.set_yticks(y)
    ax.set_yticklabels([f'{i + 1}. "{s}"' for i, s in enumerate(SENTENCES)], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('how many pieces the sentence is cut into', fontsize=10)
    ax.set_xlim(0, max(letters) * 1.16)
    ax.legend(fontsize=9.5, frameon=False, loc='upper right')
    ax.set_title('Five robot instructions, counted three ways: subword tokens sit '
                 'between whole words and single letters',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'token-counts.svg')


# --------------------------------------------------------------------------
# section 2: why pieces rather than words or letters
# --------------------------------------------------------------------------

def three_ways_to_split() -> None:
    t = _tok()
    s = SENTENCES[2]
    seen = {w for w in t.counts}
    ws = s.split()
    word_row = [w if END + w in seen else '<unk>' for w in ws]
    pieces = t.split(s)
    letters = [c for c in s if c != ' ']
    unknown = sum(1 for w in ws if END + w not in seen)
    print(f'[s2] "{s}"')
    print(f'[s2] whole words: {len(ws)} tokens, {unknown} of them unknown '
          f'({", ".join(w for w in ws if END + w not in seen)})')
    print(f'[s2] subword: {len(pieces)} tokens, 0 unknown')
    print(f'[s2] single letters: {len(letters)} tokens, 0 unknown')

    fig, ax = plt.subplots(figsize=(12.6, 5.4), facecolor='white')
    _blank(ax)
    ax.text(0.0, 4.35, f'"{s}"', fontsize=12, color=INK, family='DejaVu Sans Mono')
    rows = [
        ('one token per whole word', word_row, SLIDE, 0.34, 2.95),
        ('one token per subword piece', [p.replace(END, '␣') for p in pieces],
         LINK, 0.26, 1.75),
        ('one token per letter', letters, MUTED, 0.0, 0.55),
    ]
    right = 0.0
    for label, items, colour, cw, y in rows:
        ax.text(0.0, y + 0.82, label, fontsize=10.5, color=colour, weight='bold')
        x = 0.0
        for it in items:
            w = max(0.36, cw * len(it) + 0.16)
            bad = it == '<unk>'
            _box(ax, x, y, w, 0.56, it, face='#f2c3c3' if bad else 'white',
                 edge=GRIP if bad else colour, size=8.2, family='DejaVu Sans Mono',
                 colour=GRIP if bad else INK)
            x += w + 0.05
        ax.text(x + 0.15, y + 0.28, f'{len(items)} tokens', fontsize=10.5, color=colour,
                weight='bold', va='center')
        right = max(right, x + 2.0)
    plural = 'word' if unknown == 1 else 'words'
    ax.text(0.0, 0.0, f'The whole-word row loses the {unknown} {plural} it has never '
                      'seen, and nothing downstream can get them back.',
            fontsize=10.5, color=GRIP)
    ax.set_xlim(-0.2, right)
    ax.set_ylim(-0.3, 4.9)
    ax.set_title('The same instruction split three ways: whole words cannot spell '
                 'what they never saw, letters make the sequence long',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'three-ways-to-split.svg')


def vocabulary_size_curve() -> None:
    t = _tok()
    counts = t.counts
    merges, strengths = _train_bpe(counts, 1500)
    sizes: list[int] = []
    corpus_rate: list[float] = []
    held_rate: list[float] = []
    held = ' '.join(SENTENCES)
    held_words = len(held.split())
    alphabet = len({ch for w in counts for ch in w}) + 2
    for nm in (0, 50, 100, 150, 200, 300, 400, 500, 600, len(merges)):
        sub = {m: i for i, m in enumerate(merges[:nm])}
        cache: dict[str, list[str]] = {}

        def split(word: str) -> list[str]:
            if word in cache:
                return cache[word]
            ps = list(word)
            while len(ps) > 1:
                best: tuple[int, int] | None = None
                for i, (a, b) in enumerate(zip(ps, ps[1:])):
                    r = sub.get((a, b))
                    if r is not None and (best is None or r < best[0]):
                        best = (r, i)
                if best is None:
                    break
                i = best[1]
                ps = ps[:i] + [ps[i] + ps[i + 1]] + ps[i + 2:]
            cache[word] = ps
            return ps

        n_tok = sum(n * len(split(w)) for w, n in counts.items())
        n_w = sum(counts.values())
        h_tok = sum(len(split(END + w)) for w in held.split())
        sizes.append(alphabet + nm)
        corpus_rate.append(n_tok / n_w)
        held_rate.append(h_tok / held_words)
        print(f'[s2] vocabulary {alphabet + nm:5d} tokens -> '
              f'{n_tok / n_w:.3f} tokens per word on the training text, '
              f'{h_tok / held_words:.3f} on the five sentences')

    fig, ax = plt.subplots(figsize=(10.4, 5.4), facecolor='white')
    _plain(ax)
    ax.plot(sizes, corpus_rate, marker='o', color=LINK, lw=2,
            label='on the text the tokeniser was built from')
    ax.plot(sizes, held_rate, marker='s', color=WRIST, lw=2,
            label='on the five instructions, which it has not seen')
    last = -1e9
    for x, yc, yh in zip(sizes, corpus_rate, held_rate):
        if x - last < 55:
            continue
        last = x
        ax.text(x, yc - 0.17, f'{yc:.2f}', fontsize=8.5, color=LINK, ha='center')
        ax.text(x, yh + 0.08, f'{yh:.2f}', fontsize=8.5, color=WRIST, ha='center')
    ax.axhline(1.0, color=MUTED, ls='--', lw=1.1)
    ax.text(sizes[2], 1.06, 'one token per word', fontsize=9, color=MUTED, ha='left')
    ax.set_xlabel('how many tokens the vocabulary holds', fontsize=10)
    ax.set_ylabel('average tokens per word', fontsize=10)
    ax.set_ylim(0.8, max(corpus_rate) * 1.08)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('A bigger vocabulary gives shorter sequences, and the gain runs out',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'vocabulary-size-curve.svg')


def merge_table() -> None:
    t = _tok()
    word = END + 'gripper'
    states: list[tuple[int, str, list[str]]] = []
    ps = list(word)
    states.append((-1, 'start', list(ps)))
    for i, (a, b) in enumerate(t.merges):
        new: list[str] = []
        k = 0
        changed = False
        while k < len(ps):
            if k + 1 < len(ps) and ps[k] == a and ps[k + 1] == b:
                new.append(a + b)
                k += 2
                changed = True
            else:
                new.append(ps[k])
                k += 1
        if changed:
            ps = new
            states.append((i, f'{a} + {b}', list(ps)))
        if len(ps) == 1:
            break
    for rank, rule, st in states:
        print(f'[s2] merge {rank + 1 if rank >= 0 else 0:4d} {rule:14s} -> '
              + ' | '.join(st))

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.4), facecolor='white',
                             gridspec_kw={'width_ratios': [1.0, 1.25]})
    ax = axes[0]
    _blank(ax)
    ax.text(0.0, 10.6, 'rank', fontsize=10, color=MUTED, weight='bold')
    ax.text(1.3, 10.6, 'pair joined', fontsize=10, color=MUTED, weight='bold')
    ax.text(4.3, 10.6, 'new token', fontsize=10, color=MUTED, weight='bold')
    ax.text(6.6, 10.6, 'times seen', fontsize=10, color=MUTED, weight='bold')
    for k in range(10):
        (a, b), n = t.merges[k], t.strengths[k]
        y = 9.5 - k
        ax.text(0.2, y, str(k + 1), fontsize=10, color=INK)
        ax.text(1.3, y, f'{a.replace(END, "␣")} + {b.replace(END, "␣")}',
                fontsize=10.5, color=INK, family='DejaVu Sans Mono')
        ax.text(4.3, y, (a + b).replace(END, '␣'), fontsize=10.5, color=LINK,
                family='DejaVu Sans Mono', weight='bold')
        ax.text(7.6, y, f'{n:,}', fontsize=10, color=MUTED, ha='right')
    ax.set_xlim(-0.2, 8.0)
    ax.set_ylim(-0.5, 11.2)
    ax.set_title('The ten pairs joined first', fontsize=11.5, weight='bold', color=INK,
                 loc='left')

    ax = axes[1]
    _blank(ax)
    shown = states[:11]
    for k, (rank, rule, st) in enumerate(shown):
        y = (len(shown) - 1 - k) * 1.0
        ax.text(0.0, y + 0.28, 'start' if rank < 0 else f'after merge {rank + 1}',
                fontsize=9.5, color=MUTED)
        x = 2.6
        for p in st:
            w = max(0.42, 0.26 * len(p) + 0.16)
            _box(ax, x, y, w, 0.54, p.replace(END, '␣'),
                 face=LINK_PALE if len(st) == 1 else 'white', size=9.5,
                 family='DejaVu Sans Mono', edge=LINK)
            x += w + 0.07
        ax.text(x + 0.1, y + 0.28, f'{len(st)}', fontsize=9.5, color=MUTED, va='center')
    ax.set_xlim(-0.2, 7.2)
    ax.set_ylim(-0.3, len(shown) * 1.0 + 0.3)
    ax.set_title('␣gripper built up by those merges: eight pieces down to one',
                 fontsize=11.5, weight='bold', color=INK, loc='left')
    fig.tight_layout(w_pad=3.0)
    _save(fig, TOK_DOC, 'merge-table.svg')


# --------------------------------------------------------------------------
# section 3: the embedding table as a lookup
# --------------------------------------------------------------------------

TABLE_WORDS: list[str] = ['mug', 'cup', 'bowl', 'table', 'shelf', 'gripper',
                          'wrist', 'red', 'blue', 'pick']


def _table_rows() -> list[tuple[str, int, Arr]]:
    t, e = _tok(), _emb()
    rows = []
    for w in TABLE_WORDS:
        rows.append((END + w, t.ids[END + w], e.small[e.index[w]]))
    return rows


def _draw_table(ax: Axes, rows: list[tuple[str, int, Arr]], x0: float = 0.0,
                y0: float = 0.0, cw: float = 1.05, rh: float = 0.62,
                highlight: int | None = None, size: float = 9.0) -> None:
    n = len(rows)
    ax.text(x0 - 0.1, y0 + n * rh + 0.30, 'token', fontsize=9.5, color=MUTED,
            weight='bold', ha='left')
    ax.text(x0 + 1.55, y0 + n * rh + 0.30, 'id', fontsize=9.5, color=MUTED,
            weight='bold', ha='center')
    for j in range(6):
        ax.text(x0 + 2.2 + (j + 0.5) * cw, y0 + n * rh + 0.30, f'{j + 1}', fontsize=9.5,
                color=MUTED, weight='bold', ha='center')
    for i, (name, tid, vec) in enumerate(rows):
        y = y0 + (n - 1 - i) * rh
        on = highlight == i
        ax.text(x0 - 0.1, y + rh / 2, name.replace(END, '␣'), fontsize=9.8,
                color=LINK if on else INK, va='center', family='DejaVu Sans Mono',
                weight='bold' if on else 'normal')
        ax.text(x0 + 1.55, y + rh / 2, str(tid), fontsize=9.3, color=MUTED, va='center',
                ha='center')
        for j, v in enumerate(vec):
            ax.add_patch(Rectangle((x0 + 2.2 + j * cw, y), cw, rh,
                                   facecolor=LINK_PALE if on else 'white',
                                   edgecolor=GRID, lw=0.8))
            ax.text(x0 + 2.2 + (j + 0.5) * cw, y + rh / 2, f'{v:+.2f}', fontsize=size,
                    ha='center', va='center', color=INK)


def embedding_table() -> None:
    rows = _table_rows()
    t = _tok()
    e = _emb()
    print(f'[s3] table drawn: {len(rows)} of {len(t.vocab)} rows, 6 of '
          f'{e.full.shape[1]} numbers each')
    for name, tid, vec in rows:
        print(f'[s3] {name:9s} id {tid:4d} -> ' + ' '.join(f'{v:+.2f}' for v in vec))

    fig, ax = plt.subplots(figsize=(11.6, 5.6), facecolor='white')
    _blank(ax)
    _draw_table(ax, rows, x0=3.6, y0=0.1, highlight=0)
    ax.text(0.0, 3.15, 'the sentence said ␣mug,', fontsize=11, color=INK)
    ax.text(0.0, 2.80, f'which is token number {rows[0][1]},', fontsize=11, color=INK)
    ax.text(0.0, 2.45, f'so the table hands back row {rows[0][1]}', fontsize=11,
            color=LINK, weight='bold')
    _arrow(ax, 2.95, 2.55, 3.45, 6.0, colour=LINK, lw=1.6)
    ax.text(3.6 + 2.2 + 3 * 1.05, -0.55, 'the six learned numbers for that token',
            fontsize=10, color=MUTED, ha='center')
    ax.set_xlim(-0.2, 13.2)
    ax.set_ylim(-0.9, 7.2)
    ax.set_title('The embedding table is a lookup: one token number picks one row '
                 'of learned numbers',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'embedding-table.svg')


def lookup_as_matrix() -> None:
    rows = _table_rows()
    mat = np.array([r[2] for r in rows])
    pick = 2                                    # the row for the token for bowl
    one_hot = np.zeros(len(rows))
    one_hot[pick] = 1.0
    out = one_hot @ mat
    print(f'[s3] one-hot row for {rows[pick][0]} times the table gives '
          + ' '.join(f'{v:+.2f}' for v in out))
    print(f'[s3] column 1 of that product: '
          + ' + '.join(f'{o:.0f}x{m:+.2f}' for o, m in zip(one_hot, mat[:, 0]))
          + f' = {out[0]:+.2f}')

    fig, ax = plt.subplots(figsize=(12.0, 5.0), facecolor='white')
    _blank(ax)
    for i, v in enumerate(one_hot):
        ax.add_patch(Rectangle((i * 0.62, 3.0), 0.62, 0.62,
                               facecolor=GRIP if v else 'white', edgecolor=GRID, lw=0.8))
        ax.text((i + 0.5) * 0.62, 3.31, f'{v:.0f}', fontsize=9.5, ha='center',
                va='center', color='white' if v else INK)
    ax.text(0.0, 3.92, 'one row of 0s with a single 1, at the place of the token '
                       f'{rows[pick][0].replace(END, "␣")}',
            fontsize=10, color=MUTED)
    ax.text(len(rows) * 0.62 + 0.25, 3.31, 'x', fontsize=15, color=INK, va='center')
    _draw_table(ax, rows, x0=7.6, y0=0.1, highlight=pick, size=8.6)
    ax.text(7.6, -0.6, f'the whole table, {len(rows)} rows of 6 numbers', fontsize=10,
            color=MUTED)
    ax.text(14.4, 3.31, '=', fontsize=15, color=INK, va='center')
    for j, v in enumerate(out):
        ax.add_patch(Rectangle((15.1 + j * 0.86, 3.0), 0.86, 0.62, facecolor=LINK_PALE,
                               edgecolor=LINK, lw=0.9))
        ax.text(15.1 + (j + 0.5) * 0.86, 3.31, f'{v:+.2f}', fontsize=9, ha='center',
                va='center', color=INK)
    ax.text(15.1, 3.92, 'exactly the highlighted row', fontsize=10, color=LINK)
    ax.text(15.1, 2.25, 'column 1 works out as\n'
            + ' + '.join(f'{o:.0f}×{m:+.2f}' for o, m in zip(one_hot[:4], mat[:4, 0]))
            + f'\n+ ... = {out[0]:+.2f}', fontsize=9.5, color=MUTED, va='top')
    ax.set_xlim(-0.2, 21.0)
    ax.set_ylim(-0.9, 4.4)
    ax.set_title('The lookup is a matrix multiply in disguise, which is why libraries '
                 'call it a layer',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'lookup-as-matrix.svg')


def table_size() -> None:
    t = _tok()
    cases = [('this page’s tiny table', len(t.vocab), 6),
             ('a small model', 8_000, 256),
             ('a medium model', 32_000, 1_024),
             ('a large model', 128_000, 4_096)]
    counts = [v * d for _, v, d in cases]
    bytes_ = [c * 2 for c in counts]
    for (name, v, d), c, b in zip(cases, counts, bytes_):
        print(f'[s3] {name}: {v:,} tokens x {d} numbers = {c:,} weights, '
              f'{b / 1e6:,.1f} MB at two bytes each')

    fig, ax = plt.subplots(figsize=(10.6, 5.2), facecolor='white')
    _plain(ax)
    x = np.arange(len(cases))
    ax.bar(x, counts, color=[MUTED, LINK, PURPLE, WRIST], width=0.55)
    ax.set_yscale('log')
    for i, (c, b) in enumerate(zip(counts, bytes_)):
        mb = f'{b / 1e6:,.1f} MB' if b >= 1e6 else f'{b / 1e3:,.1f} kB'
        ax.text(i, c * 1.5, f'{c:,}\nweights\n({mb})', ha='center', fontsize=9.5,
                color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{n}\n{v:,} tokens × {d} numbers' for (n, v, d) in cases],
                       fontsize=9.5)
    ax.set_ylabel('weights in the embedding table (log scale)', fontsize=10)
    ax.set_ylim(1e3, max(counts) * 60)
    ax.set_title('The table is often one of the largest single blocks of weights '
                 'in a model',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'table-size.svg')


# --------------------------------------------------------------------------
# section 4: cosine similarity
# --------------------------------------------------------------------------

def cosine_worked() -> None:
    e = _emb()
    a = e.small[e.index['mug']]
    pairs = [('bowl', e.small[e.index['bowl']]), ('table', e.small[e.index['table']])]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0), facecolor='white')
    for ax, (name, b) in zip(axes, pairs):
        _blank(ax)
        prods = a * b
        dot = float(prods.sum())
        la, lb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        cos = dot / (la * lb)
        print(f'[s4] mug vs {name}: dot {dot:+.4f}, lengths {la:.4f} and {lb:.4f}, '
              f'cosine {cos:.3f}')
        print(f'[s4]   products ' + ' '.join(f'{p:+.4f}' for p in prods))
        head = ['number', '␣mug', f'␣{name}', 'product']
        for j, h in enumerate(head):
            ax.text(j * 1.5, 7.3, h, fontsize=9.8, color=MUTED, weight='bold',
                    ha='center')
        for i in range(6):
            y = 6.5 - i * 0.72
            ax.text(0.0, y, f'{i + 1}', fontsize=9.6, ha='center', color=MUTED)
            ax.text(1.5, y, f'{a[i]:+.2f}', fontsize=9.6, ha='center', color=INK)
            ax.text(3.0, y, f'{b[i]:+.2f}', fontsize=9.6, ha='center', color=INK)
            ax.text(4.5, y, f'{prods[i]:+.4f}', fontsize=9.6, ha='center', color=LINK)
        ax.plot([3.9, 5.1], [1.92, 1.92], color=INK, lw=1.0)
        ax.text(4.5, 1.5, f'{dot:+.4f}', fontsize=10.5, ha='center', color=LINK,
                weight='bold')
        ax.text(0.0, 0.85, f'length of ␣mug = {la:.4f}', fontsize=10, color=INK)
        ax.text(0.0, 0.40, f'length of ␣{name} = {lb:.4f}', fontsize=10, color=INK)
        ax.text(0.0, -0.20, f'cosine = {dot:+.4f} / ({la:.4f} × {lb:.4f}) '
                            f'= {cos:.3f}', fontsize=11.5, color=GRIP, weight='bold')
        ax.set_xlim(-0.8, 5.6)
        ax.set_ylim(-0.7, 7.9)
        ax.set_title(f'␣mug against ␣{name}', fontsize=11.5, weight='bold',
                     color=INK, loc='left')
    fig.suptitle('Cosine similarity worked out in full: multiply number by number, '
                 'add, divide by the two lengths',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout(w_pad=3.0)
    _save(fig, TOK_DOC, 'cosine-worked.svg')


def similarity_heatmap() -> None:
    e = _emb()
    words = ['mug', 'cup', 'bowl', 'block', 'table', 'shelf', 'gripper', 'wrist',
             'red', 'blue']
    m = np.array([[_cos(e.small[e.index[a]], e.small[e.index[b]]) for b in words]
                  for a in words])
    print('[s4] cosine table (6 numbers each):')
    for i, a in enumerate(words):
        print(f'[s4]   {a:8s} ' + ' '.join(f'{v:5.2f}' for v in m[i]))

    fig, ax = plt.subplots(figsize=(8.6, 7.4), facecolor='white')
    im = ax.imshow(m, cmap='BrBG', vmin=-1, vmax=1)
    for i in range(len(words)):
        for j in range(len(words)):
            ax.text(j, i, f'{m[i, j]:.2f}', ha='center', va='center', fontsize=8.6,
                    color='white' if abs(m[i, j]) > 0.62 else INK)
    ax.set_xticks(range(len(words)))
    ax.set_xticklabels([f'␣{w}' for w in words], rotation=45, ha='right',
                       fontsize=9.5)
    ax.set_yticks(range(len(words)))
    ax.set_yticklabels([f'␣{w}' for w in words], fontsize=9.5)
    ax.tick_params(length=0)
    fig.colorbar(im, ax=ax, shrink=0.72, label='cosine similarity')
    ax.set_title('Things used in the same way end up pointing the same way',
                 fontsize=12.5, weight='bold', color=INK, loc='left', pad=12)
    _save(fig, TOK_DOC, 'similarity-heatmap.svg')


def cosine_not_length() -> None:
    a = np.array([3.0, 1.0])
    b = np.array([6.0, 2.0])
    c = np.array([1.0, 3.0])
    rows = [('b', b), ('c', c)]
    print('[s4] a = (3, 1)')
    for name, v in rows:
        d = float(np.linalg.norm(a - v))
        print(f'[s4] a vs {name} = ({v[0]:.0f}, {v[1]:.0f}): cosine {_cos(a, v):.3f}, '
              f'straight-line distance {d:.3f}')

    fig, ax = plt.subplots(figsize=(8.6, 6.2), facecolor='white')
    _plain(ax)
    for v, colour, lab in ((a, INK, 'a = (3, 1)'), (b, LINK, 'b = (6, 2)'),
                           (c, WRIST, 'c = (1, 3)')):
        ax.add_patch(FancyArrow(0, 0, v[0], v[1], width=0.035, head_width=0.22,
                                head_length=0.3, length_includes_head=True,
                                color=colour, zorder=3))
        ax.text(v[0] + 0.18, v[1] + 0.12, lab, fontsize=11, color=colour, weight='bold')
    ax.plot([a[0], b[0]], [a[1], b[1]], ls=':', color=MUTED, lw=1.3)
    ax.plot([a[0], c[0]], [a[1], c[1]], ls=':', color=MUTED, lw=1.3)
    ax.text(4.6, 1.35, f'distance {np.linalg.norm(a - b):.2f}', fontsize=9.5,
            color=MUTED)
    ax.text(1.5, 2.3, f'distance {np.linalg.norm(a - c):.2f}', fontsize=9.5, color=MUTED)
    ax.text(0.25, 5.25, f'cosine(a, b) = {_cos(a, b):.2f}: same direction, '
                        'twice as long', fontsize=11, color=LINK, weight='bold')
    ax.text(0.25, 4.85, f'cosine(a, c) = {_cos(a, c):.2f}: nearer, but pointing '
                        'elsewhere', fontsize=11, color=WRIST, weight='bold')
    ax.set_xlim(-0.3, 7.2)
    ax.set_ylim(-0.3, 5.7)
    ax.set_xlabel('first number', fontsize=10)
    ax.set_ylabel('second number', fontsize=10)
    ax.set_aspect('equal')
    ax.set_title('Cosine asks about direction only, which is why it is used instead '
                 'of straight-line distance',
                 fontsize=12.2, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'cosine-not-length.svg')


def nearest_neighbours() -> None:
    e = _emb()
    queries = ['mug', 'gripper', 'table', 'red']
    fig, axes = plt.subplots(1, len(queries), figsize=(13.0, 4.2), facecolor='white')
    for ax, q in zip(axes, queries):
        v = e.full[e.index[q]]
        sims = sorted(((_cos(v, e.full[i]), w) for i, w in enumerate(e.words) if w != q),
                      reverse=True)[:5]
        print(f'[s4] nearest to ␣{q} (all 64 numbers): '
              + ', '.join(f'{w} {s:.3f}' for s, w in sims))
        _plain(ax)
        names = [w for _, w in sims][::-1]
        vals = [s for s, _ in sims][::-1]
        ax.barh(range(len(vals)), vals, color=LINK, height=0.62)
        for i, (val, nm) in enumerate(zip(vals, names)):
            ax.text(0.02, i, f'␣{nm}', va='center', fontsize=10, color='white')
            ax.text(val + 0.02, i, f'{val:.2f}', va='center', fontsize=9.5, color=INK)
        ax.set_yticks([])
        ax.set_xlim(0, 1.18)
        ax.set_xticks([0, 0.5, 1.0])
        ax.set_xlabel('cosine', fontsize=9.5)
        ax.set_title(f'␣{q}', fontsize=12, weight='bold', color=INK)
    fig.suptitle('The five nearest tokens to four given tokens, using all 64 numbers '
                 'of each row', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TOK_DOC, 'nearest-neighbours.svg')


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    report_text_machinery()
    sentence_into_tokens()
    common_and_rare()
    token_counts()
    three_ways_to_split()
    vocabulary_size_curve()
    merge_table()
    embedding_table()
    lookup_as_matrix()
    table_size()
    cosine_worked()
    similarity_heatmap()
    cosine_not_length()
    nearest_neighbours()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
