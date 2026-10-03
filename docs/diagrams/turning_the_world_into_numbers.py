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
        if x - last < 55 or x == sizes[0]:
            continue
        last = x
        dy = 0.12 if yc < 1.35 else -0.17
        ax.text(x, yc + dy, f'{yc:.2f}', fontsize=8.5, color=LINK, ha='center')
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
    ax.text(x0 + 1.95, y0 + n * rh + 0.30, 'id', fontsize=9.5, color=MUTED,
            weight='bold', ha='center')
    for j in range(6):
        ax.text(x0 + 2.6 + (j + 0.5) * cw, y0 + n * rh + 0.30, f'{j + 1}', fontsize=9.5,
                color=MUTED, weight='bold', ha='center')
    for i, (name, tid, vec) in enumerate(rows):
        y = y0 + (n - 1 - i) * rh
        on = highlight == i
        ax.text(x0 - 0.1, y + rh / 2, name.replace(END, '␣'), fontsize=9.8,
                color=LINK if on else INK, va='center', family='DejaVu Sans Mono',
                weight='bold' if on else 'normal')
        ax.text(x0 + 1.95, y + rh / 2, str(tid), fontsize=9.3, color=MUTED, va='center',
                ha='center')
        for j, v in enumerate(vec):
            ax.add_patch(Rectangle((x0 + 2.6 + j * cw, y), cw, rh,
                                   facecolor=LINK_PALE if on else 'white',
                                   edgecolor=GRID, lw=0.8))
            ax.text(x0 + 2.6 + (j + 0.5) * cw, y + rh / 2, f'{v:+.2f}', fontsize=size,
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
    _draw_table(ax, rows, x0=4.4, y0=0.1, highlight=0)
    ax.text(0.0, 6.95, 'the sentence said ␣mug,', fontsize=11, color=INK)
    ax.text(0.0, 6.55, f'which is token number {rows[0][1]},', fontsize=11, color=INK)
    ax.text(0.0, 6.15, f'so the table hands back row {rows[0][1]}', fontsize=11,
            color=LINK, weight='bold')
    _arrow(ax, 3.20, 6.10, 3.45, 5.99, colour=LINK, lw=1.6)
    ax.text(3.6 + 2.2 + 3 * 1.05, -0.55, 'the six learned numbers for that token',
            fontsize=10, color=MUTED, ha='center')
    ax.set_xlim(-0.2, 14.4)
    ax.set_ylim(-0.9, 8.1)
    ax.set_title('The embedding table is a lookup: one token number picks one row '
                 'of learned numbers',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'embedding-table.svg')


def lookup_as_matrix() -> None:
    rows = _table_rows()[:6]
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

    rh, n = 0.62, len(rows)
    mid = 0.1 + n * rh / 2 - 0.31
    fig, ax = plt.subplots(figsize=(12.6, 4.4), facecolor='white')
    _blank(ax)
    for i, v in enumerate(one_hot):
        ax.add_patch(Rectangle((i * 0.62, mid), 0.62, 0.62,
                               facecolor=GRIP if v else 'white', edgecolor=GRID, lw=0.8))
        ax.text((i + 0.5) * 0.62, mid + 0.31, f'{v:.0f}', fontsize=9.5, ha='center',
                va='center', color='white' if v else INK)
    ax.text(0.0, mid + 0.92, 'a row of 0s with one 1,\n'
                             f'at the place of {rows[pick][0].replace(END, "␣")}',
            fontsize=10, color=MUTED, va='bottom')
    ax.text(n * 0.62 + 0.3, mid + 0.31, '×', fontsize=15, color=INK, va='center')
    _draw_table(ax, rows, x0=6.0, y0=0.1, highlight=pick, size=8.6)
    ax.text(6.0, -0.55, f'the table, {len(rows)} rows of 6 numbers', fontsize=10,
            color=MUTED)
    ax.text(14.9, mid + 0.31, '=', fontsize=15, color=INK, va='center')
    for j, v in enumerate(out):
        ax.add_patch(Rectangle((15.6 + j * 0.86, mid), 0.86, 0.62, facecolor=LINK_PALE,
                               edgecolor=LINK, lw=0.9))
        ax.text(15.6 + (j + 0.5) * 0.86, mid + 0.31, f'{v:+.2f}', fontsize=9,
                ha='center', va='center', color=INK)
    ax.text(15.6, mid + 0.80, 'exactly the highlighted row', fontsize=10, color=LINK)
    terms = [f'{o:.0f}×{m:+.2f}' for o, m in zip(one_hot, mat[:, 0])]
    ax.text(15.6, mid - 0.28, 'number 1 of the answer is\n'
            + ' + '.join(terms[:3]) + '\n+ ' + ' + '.join(terms[3:])
            + f'\n= {out[0]:+.2f}', fontsize=9.2, color=MUTED, va='top')
    ax.set_xlim(-0.2, 21.6)
    ax.set_ylim(-1.4, 4.9)
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
    ax.set_xticklabels([f'{n}\n{v:,} × {d}' for (n, v, d) in cases], fontsize=9.5)
    ax.text(0.02, 0.94, 'each label is the number of tokens times the numbers per token',
            transform=ax.transAxes, ha='left', fontsize=9, color=MUTED)
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
    for v, colour, lab, dy in ((a, INK, 'a = (3, 1)', -0.38), (b, LINK, 'b = (6, 2)', 0.14),
                               (c, WRIST, 'c = (1, 3)', 0.18)):
        ax.add_patch(FancyArrow(0, 0, v[0], v[1], width=0.035, head_width=0.22,
                                head_length=0.3, length_includes_head=True,
                                color=colour, zorder=3))
        ax.text(v[0] + 0.18, v[1] + dy, lab, fontsize=11, color=colour, weight='bold')
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


# --------------------------------------------------------------------------
# section 5: order, learned position vectors and rotary position embedding
# --------------------------------------------------------------------------

PAIR_A: str = 'the mug is in the bowl'
PAIR_B: str = 'the bowl is in the mug'


def same_tokens_different_order() -> None:
    t, e = _tok(), _emb()
    rows_a = [(p, t.ids[p], e.small[e.index[p[1:]]]) for p in t.split(PAIR_A)]
    rows_b = [(p, t.ids[p], e.small[e.index[p[1:]]]) for p in t.split(PAIR_B)]
    sum_a = np.sum([r[2] for r in rows_a], axis=0)
    sum_b = np.sum([r[2] for r in rows_b], axis=0)
    print(f'[s5] "{PAIR_A}" -> {[r[0] for r in rows_a]}')
    print(f'[s5] "{PAIR_B}" -> {[r[0] for r in rows_b]}')
    print('[s5] sum of the six rows, first sentence:  '
          + ' '.join(f'{v:+.2f}' for v in sum_a))
    print('[s5] sum of the six rows, second sentence: '
          + ' '.join(f'{v:+.2f}' for v in sum_b))
    print(f'[s5] the two sums differ by {np.abs(sum_a - sum_b).max():.4f} at most')

    fig, ax = plt.subplots(figsize=(13.0, 5.4), facecolor='white')
    _blank(ax)
    right = 0.0
    for k, (sent, rows, s) in enumerate(((PAIR_A, rows_a, sum_a),
                                         (PAIR_B, rows_b, sum_b))):
        y = 2.9 - k * 1.65
        ax.text(0.0, y + 0.95, f'"{sent}"', fontsize=11.5, color=INK,
                family='DejaVu Sans Mono')
        x = _piece_row(ax, [r[0] for r in rows], [r[1] for r in rows], y, x0=0.0,
                       size=9.5)
        ax.text(x + 0.2, y + 0.31, 'add the six rows:', fontsize=10, color=MUTED,
                va='center')
        for j, v in enumerate(s):
            ax.add_patch(Rectangle((x + 2.6 + j * 0.78, y), 0.78, 0.62,
                                   facecolor='#ddeedd' if k == 0 else '#ddeedd',
                                   edgecolor=SLIDE, lw=0.9))
            ax.text(x + 2.6 + (j + 0.5) * 0.78, y + 0.31, f'{v:+.2f}', fontsize=8.6,
                    ha='center', va='center', color=INK)
        right = max(right, x + 2.6 + 6 * 0.78 + 0.3)
    ax.text(0.0, 0.25, 'The two sums are the same to every decimal place, so a layer '
                       'that only adds its inputs up cannot tell the two sentences '
                       'apart.', fontsize=11, color=GRIP)
    ax.set_xlim(-0.2, right)
    ax.set_ylim(0.0, 4.4)
    ax.set_title('The same tokens in a different order: without position, nothing in '
                 'the numbers says which is which',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'same-tokens-different-order.svg')


def position_vectors_added() -> None:
    e = _emb()
    rng = np.random.default_rng(23)
    pos = np.round(rng.normal(0.0, 0.25, size=(6, 6)), 2)
    tok_vec = e.small[e.index['mug']]
    at1 = tok_vec + pos[1]
    at4 = tok_vec + pos[4]
    print('[s5] learned position rows (simulated, seed 23):')
    for i in range(6):
        print(f'[s5]   position {i}: ' + ' '.join(f'{v:+.2f}' for v in pos[i]))
    print('[s5] ␣mug at position 1 -> ' + ' '.join(f'{v:+.2f}' for v in at1))
    print('[s5] ␣mug at position 4 -> ' + ' '.join(f'{v:+.2f}' for v in at4))
    print(f'[s5] cosine between the two: {_cos(at1, at4):.3f}')

    fig, ax = plt.subplots(figsize=(12.2, 5.6), facecolor='white')
    _blank(ax)
    for i in range(6):
        y = 5.0 - i * 0.68
        ax.text(0.0, y + 0.31, f'position {i}', fontsize=9.6, color=MUTED, va='center')
        for j, v in enumerate(pos[i]):
            on = i in (1, 4)
            ax.add_patch(Rectangle((1.9 + j * 0.82, y), 0.82, 0.62,
                                   facecolor='#f6ddc8' if on else 'white',
                                   edgecolor=GRID, lw=0.8))
            ax.text(1.9 + (j + 0.5) * 0.82, y + 0.31, f'{v:+.2f}', fontsize=8.6,
                    ha='center', va='center', color=INK)
    ax.text(1.9, 5.78, 'the learned position table, one row per place in the sentence',
            fontsize=10, color=MUTED)
    for k, (lab, vec, colour, y) in enumerate(
            (('␣mug', tok_vec, LINK, 3.1), ('+ position 1', pos[1], WRIST, 2.42),
             ('= input at 1', at1, SLIDE, 1.74),
             ('␣mug', tok_vec, LINK, 0.86), ('+ position 4', pos[4], WRIST, 0.18),
             ('= input at 4', at4, SLIDE, -0.50))):
        ax.text(7.3, y + 0.31, lab, fontsize=10, color=colour, va='center',
                weight='bold' if lab.startswith('=') else 'normal')
        for j, v in enumerate(vec):
            ax.add_patch(Rectangle((9.3 + j * 0.82, y), 0.82, 0.62,
                                   facecolor='#ddeedd' if lab.startswith('=') else 'white',
                                   edgecolor=colour, lw=0.9))
            ax.text(9.3 + (j + 0.5) * 0.82, y + 0.31, f'{v:+.2f}', fontsize=8.6,
                    ha='center', va='center', color=INK)
    ax.set_xlim(-0.2, 14.6)
    ax.set_ylim(-0.9, 6.3)
    ax.set_title('Learned position vectors: the row for the place is added to the row '
                 'for the token',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'position-vectors-added.svg')


def _rope(vec: Arr, pos: int, base: float = 100.0) -> Arr:
    """Rotate each neighbouring pair of numbers by an angle that grows with position."""
    out = vec.copy()
    for k in range(len(vec) // 2):
        theta = base ** (-2.0 * k / len(vec))
        ang = pos * theta
        x, y = vec[2 * k], vec[2 * k + 1]
        out[2 * k] = x * np.cos(ang) - y * np.sin(ang)
        out[2 * k + 1] = x * np.sin(ang) + y * np.cos(ang)
    return out


def rope_rotation() -> None:
    e = _emb()
    v = e.small[e.index['mug']]
    base = 100.0
    thetas = [base ** (-2.0 * k / 6) for k in range(3)]
    print('[s5] rotary angles per step: '
          + ', '.join(f'pair {k + 1}: {t:.4f} radians' for k, t in enumerate(thetas)))
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.6), facecolor='white')
    for k, ax in enumerate(axes):
        _plain(ax)
        x0, y0 = v[2 * k], v[2 * k + 1]
        r = float(np.hypot(x0, y0))
        ang0 = np.linspace(0, 2 * np.pi, 200)
        ax.plot(r * np.cos(ang0), r * np.sin(ang0), color=GRID, lw=1.0)
        for p in range(6):
            rot = _rope(v, p, base)
            px, py = rot[2 * k], rot[2 * k + 1]
            col = plt.get_cmap('viridis')(p / 5.0)
            ax.add_patch(FancyArrow(0, 0, px, py, width=0.008 * r, head_width=0.06 * r,
                                    head_length=0.08 * r, length_includes_head=True,
                                    color=col, zorder=3))
            ax.text(px * 1.26, py * 1.26, str(p), fontsize=10, color=col, ha='center',
                    va='center', weight='bold')
            if k == 0:
                print(f'[s5] pair 1 at position {p}: ({px:+.3f}, {py:+.3f})')
        lim = r * 1.5
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect('equal')
        ax.axhline(0, color=GRID, lw=0.8)
        ax.axvline(0, color=GRID, lw=0.8)
        ax.set_xlabel(f'number {2 * k + 1}', fontsize=9.5)
        ax.set_ylabel(f'number {2 * k + 2}', fontsize=9.5)
        ax.set_title(f'pair {k + 1}: turns {thetas[k]:.4f} radians per step',
                     fontsize=11, weight='bold', color=INK)
    fig.suptitle('Rotary position embedding turns each pair of numbers by an angle '
                 'that grows with the place in the sentence (token ␣mug, '
                 'positions 0 to 5)', fontsize=12.2, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TOK_DOC, 'rope-rotation.svg')


def rope_relative() -> None:
    e = _emb()
    q = e.full[e.index['mug']]
    k = e.full[e.index['bowl']]
    base = 10_000.0
    cases = [(0, 3), (2, 5), (7, 10), (20, 23)]
    print('[s5] dot product of the rotated rows, for places the same gap apart:')
    for m, n in cases:
        d = float(_rope(q, m, base) @ _rope(k, n, base))
        print(f'[s5]   query at {m:3d}, key at {n:3d} (gap {n - m}): {d:+.6f}')
    gaps = np.arange(0, 61)
    dots = [float(_rope(q, 5, base) @ _rope(k, 5 + int(g), base)) for g in gaps]
    plain = float(q @ k)
    print(f'[s5] without any rotation the dot product is {plain:+.6f} whatever the gap')
    print(f'[s5] with rotation it runs from {min(dots):+.4f} to {max(dots):+.4f} '
          'as the gap grows')

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8), facecolor='white',
                            gridspec_kw={'width_ratios': [1.0, 1.25]})
    ax = axes[0]
    _blank(ax)
    ax.text(0.0, 4.6, 'query at', fontsize=10, color=MUTED, weight='bold')
    ax.text(2.0, 4.6, 'key at', fontsize=10, color=MUTED, weight='bold')
    ax.text(3.9, 4.6, 'gap', fontsize=10, color=MUTED, weight='bold')
    ax.text(5.4, 4.6, 'dot product', fontsize=10, color=MUTED, weight='bold')
    for i, (m, n) in enumerate(cases):
        y = 3.9 - i * 0.72
        d = float(_rope(q, m, base) @ _rope(k, n, base))
        ax.text(0.5, y, str(m), fontsize=10.5, color=INK, ha='center')
        ax.text(2.4, y, str(n), fontsize=10.5, color=INK, ha='center')
        ax.text(4.1, y, str(n - m), fontsize=10.5, color=INK, ha='center')
        ax.text(6.3, y, f'{d:+.6f}', fontsize=10.5, color=LINK, ha='center',
                weight='bold')
    ax.text(0.0, 0.5, 'Four different places, one gap of 3, one answer.', fontsize=10.5,
            color=SLIDE)
    ax.set_xlim(-0.2, 7.6)
    ax.set_ylim(0.0, 5.2)
    ax.set_title('What the rotated numbers carry is the gap',
                 fontsize=11.5, weight='bold', color=INK, loc='left')

    ax = axes[1]
    _plain(ax)
    ax.plot(gaps, dots, marker='o', ms=3, color=LINK, lw=1.6,
            label='after rotating both rows by their place')
    ax.axhline(plain, color=MUTED, ls='--', lw=1.3,
               label=f'no rotation at all: always {plain:+.3f}')
    ax.set_xlabel('gap between the two places', fontsize=10)
    ax.set_ylabel('dot product of the two rows', fontsize=10)
    ax.set_ylim(min(dots) - 0.6, plain + 0.9)
    ax.legend(fontsize=9.5, frameon=False, loc='lower left')
    ax.set_title('Rotating pulls the score away from its no-gap value as the gap grows',
                 fontsize=11.5, weight='bold', color=INK, loc='left')
    fig.tight_layout(w_pad=2.5)
    _save(fig, TOK_DOC, 'rope-relative.svg')


# --------------------------------------------------------------------------
# section 6: what the geometry is really like
# --------------------------------------------------------------------------

SHADOW_WORDS: list[str] = ['mug', 'bowl', 'box', 'table', 'shelf', 'gripper', 'wrist',
                           'red', 'green', 'pick', 'place', 'slowly']


def two_shadows() -> None:
    e = _emb()
    rng = np.random.default_rng(5)
    v = np.array([e.full[e.index[w]] for w in SHADOW_WORDS])
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.4), facecolor='white')
    for k, ax in enumerate(axes):
        plane = rng.normal(size=(e.full.shape[1], 2))
        plane /= np.linalg.norm(plane, axis=0, keepdims=True)
        xy = v @ plane
        _plain(ax)
        ax.scatter(xy[:, 0], xy[:, 1], s=36, color=LINK, zorder=3)
        centre = xy.mean(axis=0)
        span = float(np.abs(xy - centre).max())
        for (x, y), w in zip(xy, SHADOW_WORDS):
            d = np.array([x, y]) - centre
            d = d / (np.linalg.norm(d) + 1e-9)
            ax.text(x + d[0] * span * 0.24, y + d[1] * span * 0.24, w, fontsize=8.8,
                    color=INK, ha='center', va='center')
        d_mug_bowl = float(np.linalg.norm(xy[0] - xy[1]))
        d_mug_grip = float(np.linalg.norm(xy[0] - xy[5]))
        print(f'[s6] shadow {k + 1}: ␣mug to ␣bowl {d_mug_bowl:.3f}, '
              f'␣mug to ␣gripper {d_mug_grip:.3f}')
        ax.margins(0.22)
        ax.set_xlabel('first made-up direction', fontsize=9.5)
        ax.set_ylabel('second made-up direction', fontsize=9.5)
        ax.set_title(f'shadow {k + 1}', fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('Two flat pictures of the same 64 numbers per token: the picture '
                 'moves, the table does not',
                 fontsize=12.4, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TOK_DOC, 'two-shadows.svg')


def shadow_distorts() -> None:
    e = _emb()
    rng = np.random.default_rng(5)
    words = e.words
    full = e.full
    small = e.small
    plane = rng.normal(size=(full.shape[1], 2))
    plane /= np.linalg.norm(plane, axis=0, keepdims=True)
    flat = full @ plane
    true_c, flat_c, six_c = [], [], []
    for i in range(len(words)):
        for j in range(i + 1, len(words)):
            true_c.append(_cos(full[i], full[j]))
            flat_c.append(_cos(flat[i], flat[j]))
            six_c.append(_cos(small[i], small[j]))
    true_c, flat_c, six_c = np.array(true_c), np.array(flat_c), np.array(six_c)
    r_flat = float(np.corrcoef(true_c, flat_c)[0, 1])
    r_six = float(np.corrcoef(true_c, six_c)[0, 1])
    print(f'[s6] {len(true_c)} pairs of tokens')
    print(f'[s6] cosine in the flat picture against the real cosine: '
          f'correlation {r_flat:.3f}, biggest error {np.abs(flat_c - true_c).max():.3f}')
    print(f'[s6] cosine with only the first 6 numbers: correlation {r_six:.3f}, '
          f'biggest error {np.abs(six_c - true_c).max():.3f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.2), facecolor='white')
    for ax, vals, name, colour, r in ((axes[0], flat_c, 'two directions only', GRIP,
                                       r_flat),
                                      (axes[1], six_c, 'the first six numbers', WRIST,
                                       r_six)):
        _plain(ax)
        ax.scatter(true_c, vals, s=9, color=colour, alpha=0.45)
        ax.plot([-1, 1], [-1, 1], ls='--', color=MUTED, lw=1.2)
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        ax.set_aspect('equal')
        ax.set_xlabel('cosine using all 64 numbers', fontsize=10)
        ax.set_ylabel(f'cosine using {name}', fontsize=10)
        ax.set_title(f'{name}: correlation {r:.2f}', fontsize=11.5, weight='bold',
                     color=INK)
    fig.suptitle('Every pair of tokens in the table: squashing the rows down moves '
                 'the answer, sometimes a long way',
                 fontsize=12.4, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, TOK_DOC, 'shadow-distorts.svg')


def one_row_many_meanings() -> None:
    t, e = _tok(), _emb()
    sents = ['pick up the mug and put it on the shelf',
             'pick up the bolt and put it on the shelf']
    row = e.small[e.index['it']]
    print('[s6] the row for ␣it is ' + ' '.join(f'{v:+.2f}' for v in row)
          + f', token number {t.ids[END + "it"]}')
    for s in sents:
        print(f'[s6] "{s}" -> {t.split(s)}')

    fig, ax = plt.subplots(figsize=(12.6, 4.8), facecolor='white')
    _blank(ax)
    right = 0.0
    for k, s in enumerate(sents):
        y = 3.3 - k * 0.95
        pieces = t.split(s)
        x = 0.0
        for p in pieces:
            w = max(0.52, 0.27 * len(p) + 0.16)
            on = p == END + 'it'
            _box(ax, x, y, w, 0.58, p.replace(END, '␣'),
                 face='#f6ddc8' if on else 'white', edge=WRIST if on else GRID,
                 size=9.2, family='DejaVu Sans Mono')
            if on:
                _arrow(ax, x + w / 2, y, 6.2, 1.55, colour=WRIST, lw=1.4)
            x += w + 0.07
        ax.text(x + 0.25, y + 0.29, '␣it means the '
                + ('mug' if k == 0 else 'bolt'), fontsize=10.5, color=INK, va='center')
        right = max(right, x + 3.6)
    for j, v in enumerate(row):
        ax.add_patch(Rectangle((4.6 + j * 0.86, 0.9), 0.86, 0.62, facecolor='#f6ddc8',
                               edgecolor=WRIST, lw=0.9))
        ax.text(4.6 + (j + 0.5) * 0.86, 1.21, f'{v:+.2f}', fontsize=9, ha='center',
                va='center', color=INK)
    ax.text(4.6, 0.52, f'one row, token number {t.ids[END + "it"]}, the same in both '
                       'sentences', fontsize=10.5, color=WRIST)
    ax.text(0.0, 0.0, 'The table cannot hold what ␣it refers to, because the '
                      'table is looked up before anything has read the sentence.',
            fontsize=10.5, color=MUTED)
    ax.set_xlim(-0.2, right)
    ax.set_ylim(-0.3, 4.3)
    ax.set_title('One token, one row, two meanings: the embedding is a starting point '
                 'and not an answer',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, TOK_DOC, 'one-row-many-meanings.svg')


# ==========================================================================
# 02_pictures-sound-and-robot-states
# ==========================================================================

def _scene(size: int = 224) -> Arr:
    """A simulated photo of a blue mug on a pale table, as three grids of 0 to 255."""
    rng = np.random.default_rng(31)
    yy, xx = np.mgrid[0:size, 0:size].astype(float)
    r = 196 - 26 * (yy / size)
    g = 190 - 24 * (yy / size)
    b = 176 - 22 * (yy / size)
    cx, cy, rad = size * 0.46, size * 0.56, size * 0.22
    body = ((xx - cx) ** 2 + (yy - cy) ** 2) < rad ** 2
    ring = (np.abs(np.hypot(xx - (cx + rad * 1.15), yy - cy) - rad * 0.42)
            < rad * 0.13) & (xx > cx + rad * 0.6)
    shade = 1.0 - 0.35 * (yy - (cy - rad)) / (2 * rad)
    for ch, base in ((r, 58.0), (g, 92.0), (b, 184.0)):
        ch[body] = base * shade[body]
        ch[ring] = base * 0.78
    gloss = (((xx - (cx - rad * 0.35)) ** 2 + (yy - (cy - rad * 0.45)) ** 2)
             < (rad * 0.22) ** 2)
    for ch in (r, g, b):
        ch[gloss] = np.minimum(255.0, ch[gloss] + 120.0)
    pic = np.stack([r, g, b])
    pic = pic + rng.normal(0.0, 3.5, size=pic.shape)
    return np.clip(np.round(pic), 0, 255)


SCENE: Arr | None = None


def _pic() -> Arr:
    global SCENE
    if SCENE is None:
        SCENE = _scene()
    return SCENE


def _show_rgb(ax: Axes, pic: Arr) -> None:
    ax.imshow(np.transpose(pic, (1, 2, 0)).astype(np.uint8), interpolation='nearest')
    _blank(ax)


# --------------------------------------------------------------------------
# section 1: a colour photo is three grids
# --------------------------------------------------------------------------

CROP: tuple[int, int, int] = (96, 96, 8)        # top row, left column, size


def three_colour_grids() -> None:
    pic = _pic()
    r0, c0, n = CROP
    crop = pic[:, r0:r0 + n, c0:c0 + n]
    names = ['red', 'green', 'blue']
    for k, nm in enumerate(names):
        print(f'[p1] {nm} grid of the 8 by 8 crop, first row: '
              + ' '.join(f'{v:.0f}' for v in crop[k, 0]))
        print(f'[p1] {nm}: lowest {crop[k].min():.0f}, highest {crop[k].max():.0f}, '
              f'average {crop[k].mean():.1f}')
    print(f'[p1] the whole photo is 3 x {pic.shape[1]} x {pic.shape[2]} = '
          f'{3 * pic.shape[1] * pic.shape[2]:,} numbers')

    fig = plt.figure(figsize=(13.2, 4.6), facecolor='white')
    gs = fig.add_gridspec(1, 5, width_ratios=[1.25, 0.08, 1, 1, 1], wspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    _show_rgb(ax, pic)
    ax.add_patch(Rectangle((c0 - 0.5, r0 - 0.5), n, n, fill=False, edgecolor=GRIP,
                           lw=2.0))
    ax.set_title(f'the photo, {pic.shape[1]} by {pic.shape[2]} pixels',
                 fontsize=10.5, weight='bold', color=INK)
    ax.text(0.5, -0.07, f'the red square is the 8 by 8 crop below',
            transform=ax.transAxes, ha='center', fontsize=9.5, color=GRIP)
    for k, (nm, cmap) in enumerate(zip(names, ('Reds', 'Greens', 'Blues'))):
        ax = fig.add_subplot(gs[0, 2 + k])
        _grid_of_numbers(ax, crop[k], fmt='{:.0f}', cmap=cmap, vmin=0, vmax=255,
                         size=7.4)
        ax.set_title(f'{nm}: 0 to 255', fontsize=10.5, weight='bold', color=INK)
    fig.suptitle('A colour photo is three grids of brightness numbers, one for red, '
                 'one for green and one for blue',
                 fontsize=12.5, weight='bold', color=INK)
    _save(fig, STA_DOC, 'three-colour-grids.svg')


def scaling_the_values() -> None:
    pic = _pic()
    r0, c0, n = CROP
    crop = pic[:, r0:r0 + 4, c0:c0 + 4]
    zero_one = crop / 255.0
    mean = pic.mean(axis=(1, 2))
    std = pic.std(axis=(1, 2))
    standard = (crop - mean[:, None, None]) / std[:, None, None]
    print('[p1] whole-photo average per channel: '
          + ' '.join(f'{v:.1f}' for v in mean))
    print('[p1] whole-photo spread per channel: ' + ' '.join(f'{v:.1f}' for v in std))
    print('[p1] red crop raw first row: ' + ' '.join(f'{v:.0f}' for v in crop[0, 0]))
    print('[p1] red crop divided by 255: '
          + ' '.join(f'{v:.3f}' for v in zero_one[0, 0]))
    print('[p1] red crop standardised: ' + ' '.join(f'{v:+.2f}' for v in standard[0, 0]))
    print(f'[p1] standardised crop: average {standard.mean():+.2f}, '
          f'spread {standard.std():.2f}')

    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.4), facecolor='white')
    for ax, grid, title, fmt, cmap in (
            (axes[0], crop[0], 'as the camera gives it: 0 to 255', '{:.0f}', 'Reds'),
            (axes[1], zero_one[0], 'divided by 255: 0 to 1', '{:.3f}', 'Reds'),
            (axes[2], standard[0],
             f'minus {mean[0]:.1f}, divided by {std[0]:.1f}', '{:+.2f}', 'coolwarm')):
        _grid_of_numbers(ax, grid, fmt=fmt, cmap=cmap, size=9.0)
        ax.set_title(title, fontsize=10.8, weight='bold', color=INK)
    fig.suptitle('The same four by four corner of the red grid, written three ways',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'scaling-the-values.svg')


def why_scale() -> None:
    """Fit the same straight line twice, once on raw pixel values and once on scaled."""
    rng = np.random.default_rng(7)
    n = 400
    raw = np.column_stack([rng.uniform(0, 255, n), rng.uniform(0, 1, n)])
    truth = np.array([0.004, 2.0])
    y = raw @ truth + rng.normal(0, 0.05, n)
    scaled = (raw - raw.mean(0)) / raw.std(0)
    y_s = y - y.mean()

    def run(x: Arr, target: Arr, steps: int) -> tuple[list[float], float]:
        h = 2.0 * (x.T @ x) / len(target)
        ev = np.linalg.eigvalsh(h)
        lr = 1.8 / float(ev.max())
        w = np.zeros(2)
        hist = []
        for _ in range(steps):
            err = x @ w - target
            hist.append(float(np.mean(err ** 2)))
            w = w - lr * (2.0 / len(target)) * (x.T @ err)
        return hist, lr

    steps = 4000
    raw_hist, lr_raw = run(raw, y, steps)
    sc_hist, lr_sc = run(scaled, y_s, steps)
    floor = float(np.mean((y - raw @ np.linalg.lstsq(raw, y, rcond=None)[0]) ** 2))
    print(f'[p1] best possible average squared error {floor:.5f}')
    print(f'[p1] raw 0 to 255: biggest learning rate that does not blow up '
          f'{lr_raw:.2e}; loss {raw_hist[0]:.3f} -> {raw_hist[299]:.4f} at step 300 '
          f'-> {raw_hist[-1]:.4f} at step {steps}')
    print(f'[p1] scaled: biggest learning rate {lr_sc:.2e}; loss {sc_hist[0]:.3f} '
          f'-> {sc_hist[299]:.5f} at step 300 -> {sc_hist[-1]:.5f} at step {steps}')
    reach = next((i for i, v in enumerate(raw_hist) if v <= sc_hist[299]), None)
    print(f'[p1] the raw run reaches the scaled run’s 300-step loss at step '
          f'{reach if reach is not None else f"beyond {steps}"}')
    curv = []
    for name, x in (('raw 0 to 255', raw), ('scaled', scaled)):
        h = 2.0 * (x.T @ x) / len(y)
        ev = np.linalg.eigvalsh(h)
        curv.append((name, float(ev.max() / ev.min())))
        print(f'[p1] {name}: steepest direction {ev.max():.2f}, flattest {ev.min():.4f}, '
              f'ratio {ev.max() / ev.min():,.0f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(raw_hist, color=GRIP, lw=2,
            label=f'raw 0 to 255, learning rate {lr_raw:.1e}')
    ax.plot(sc_hist, color=SLIDE, lw=2, label=f'scaled, learning rate {lr_sc:.1e}')
    ax.axhline(floor, color=MUTED, ls='--', lw=1.2, label='the best a line can do')
    ax.set_yscale('log')
    ax.set_xlabel('training step', fontsize=10)
    ax.set_ylabel('average squared error (log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title(f'Each run at the fastest learning rate it can take, {steps:,} steps',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    names = [c[0] for c in curv]
    ratios = [c[1] for c in curv]
    ax.bar(names, ratios, color=[GRIP, SLIDE], width=0.5)
    for i, v in enumerate(ratios):
        ax.text(i, v * 1.6, f'{v:,.0f}', ha='center', fontsize=12, color=INK,
                weight='bold')
    ax.set_yscale('log')
    ax.set_ylim(0.5, max(ratios) * 30)
    ax.set_ylabel('steepest direction divided by flattest', fontsize=10)
    ax.set_title('Why: one input runs over a range 255 times wider',
                 fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('Scaling the inputs is not tidiness: it sets how fast training is '
                 'allowed to go', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'why-scale.svg')


# --------------------------------------------------------------------------
# section 2: patches
# --------------------------------------------------------------------------

def patch_grid() -> None:
    pic = _pic()
    size = pic.shape[1]
    p = 16
    across = size // p
    total = across * across
    print(f'[p2] {size} by {size} pixels cut into {p} by {p} patches gives '
          f'{across} by {across} = {total} patches')
    print(f'[p2] one patch holds {p} x {p} x 3 = {p * p * 3} numbers')

    fig, ax = plt.subplots(figsize=(7.4, 7.4), facecolor='white')
    _show_rgb(ax, pic)
    for i in range(across + 1):
        ax.axhline(i * p - 0.5, color='white', lw=0.7, alpha=0.85)
        ax.axvline(i * p - 0.5, color='white', lw=0.7, alpha=0.85)
    pr, pc = 6, 5
    ax.add_patch(Rectangle((pc * p - 0.5, pr * p - 0.5), p, p, fill=False,
                           edgecolor=GRIP, lw=2.4))
    ax.annotate(f'patch {pr * across + pc + 1}',
                xy=(pc * p + p, pr * p + p / 2), xytext=(size - 30, pr * p + p * 2.4),
                color=GRIP, fontsize=11, ha='right', weight='bold',
                arrowprops=dict(arrowstyle='-|>', color=GRIP, lw=1.4))
    ax.set_title(f'{size} by {size} pixels, cut into {p} by {p} squares: '
                 f'{across} × {across} = {total} patches',
                 fontsize=12.2, weight='bold', color=INK)
    _save(fig, STA_DOC, 'patch-grid.svg')


def patch_to_vector() -> None:
    pic = _pic()
    p = 16
    pr, pc = 6, 5
    patch = pic[:, pr * p:(pr + 1) * p, pc * p:(pc + 1) * p]
    flat = patch.reshape(-1) / 255.0
    rng = np.random.default_rng(13)
    width = 32
    proj = rng.normal(0, 1.0 / np.sqrt(len(flat)), size=(len(flat), width))
    vec = flat @ proj
    print(f'[p2] the chosen patch flattens to {len(flat)} numbers; first eight after '
          'dividing by 255: ' + ' '.join(f'{v:.3f}' for v in flat[:8]))
    print(f'[p2] after the learned matrix of {len(flat)} by {width} it is {width} '
          'numbers; first six: ' + ' '.join(f'{v:+.3f}' for v in vec[:6]))
    print(f'[p2] that matrix holds {len(flat) * width:,} weights')

    fig = plt.figure(figsize=(13.0, 4.4), facecolor='white')
    gs = fig.add_gridspec(1, 3, width_ratios=[0.8, 1.5, 1.5], wspace=0.3)
    ax = fig.add_subplot(gs[0, 0])
    _show_rgb(ax, patch)
    ax.set_title(f'one patch,\n{p} by {p} pixels', fontsize=10.5, weight='bold',
                 color=INK)
    ax = fig.add_subplot(gs[0, 1])
    _blank(ax)
    for i in range(7):
        ax.add_patch(Rectangle((i * 1.5, 1.0), 1.5, 0.6, facecolor=LINK_PALE,
                               edgecolor=LINK, lw=0.7))
        ax.text((i + 0.5) * 1.5, 1.3, f'{flat[i]:.2f}', fontsize=9.0, ha='center',
                va='center', color=INK)
    ax.text(7 * 1.5 + 0.25, 1.3, f'... {len(flat)} in all', fontsize=10, color=MUTED,
            va='center')
    ax.text(0.0, 2.0, 'laid out in one line: red grid, then green, then blue',
            fontsize=10, color=MUTED)
    ax.text(0.0, 0.45, f'{p} × {p} × 3 = {len(flat)} numbers, each divided '
                       'by 255', fontsize=10.5, color=INK)
    ax.set_xlim(-0.2, 13.6)
    ax.set_ylim(0.0, 2.6)
    ax.set_title('flattened', fontsize=10.5, weight='bold', color=INK)
    ax = fig.add_subplot(gs[0, 2])
    _blank(ax)
    for i in range(6):
        ax.add_patch(Rectangle((i * 1.85, 1.0), 1.85, 0.6, facecolor='#ddeedd',
                               edgecolor=SLIDE, lw=0.7))
        ax.text((i + 0.5) * 1.85, 1.3, f'{vec[i]:+.2f}', fontsize=9.0, ha='center',
                va='center', color=INK)
    ax.text(6 * 1.85 + 0.25, 1.3, f'... {width} in all', fontsize=10, color=MUTED,
            va='center')
    ax.text(0.0, 2.0, f'times a learned {len(flat)} by {width} matrix',
            fontsize=10, color=MUTED)
    ax.text(0.0, 0.45, f'that matrix alone holds {len(flat) * width:,} weights',
            fontsize=10.5, color=INK)
    ax.set_xlim(-0.2, 13.6)
    ax.set_ylim(0.0, 2.6)
    ax.set_title('one token for the transformer', fontsize=10.5, weight='bold',
                 color=INK)
    fig.suptitle('A patch becomes one token: flatten it, then multiply it by one '
                 'learned matrix', fontsize=12.5, weight='bold', color=INK, y=1.06)
    _save(fig, STA_DOC, 'patch-to-vector.svg')


def patch_count_cost() -> None:
    cases = [(224, 16), (224, 14), (336, 14), (448, 16), (896, 16)]
    rows = []
    for size, p in cases:
        across = size // p
        tok = across * across
        rows.append((size, p, across, tok, tok * tok))
        print(f'[p2] {size} by {size} with {p} by {p} patches: {across} × {across} '
              f'= {tok:,} tokens, {tok * tok:,} token pairs for attention')
    base = rows[0][4]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    labels = [f'{s}\n{p} px patches' for s, p, _, _, _ in rows]
    toks = [r[3] for r in rows]
    ax.bar(labels, toks, color=LINK, width=0.55)
    for i, v in enumerate(toks):
        ax.text(i, v * 1.04, f'{v:,}', ha='center', fontsize=10, color=INK)
    ax.set_ylabel('tokens the model must read', fontsize=10)
    ax.set_ylim(0, max(toks) * 1.2)
    ax.set_title('How many tokens one photo turns into', fontsize=11.5, weight='bold',
                 color=INK)
    ax = axes[1]
    _plain(ax)
    pairs = [r[4] / base for r in rows]
    ax.bar(labels, pairs, color=GRIP, width=0.55)
    for i, v in enumerate(pairs):
        ax.text(i, v * 1.3, f'×{v:,.0f}', ha='center', fontsize=10, color=INK)
    ax.set_yscale('log')
    ax.set_ylim(0.5, max(pairs) * 8)
    ax.set_ylabel('attention work, as a multiple of the first case', fontsize=10)
    ax.set_title('What that costs: work grows with the square of the token count',
                 fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('Patch size is the knob: smaller patches see more detail and cost '
                 'far more', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'patch-count-cost.svg')


# --------------------------------------------------------------------------
# section 3: depth pictures and point clouds
# --------------------------------------------------------------------------

def _depth(rows: int = 12, cols: int = 12) -> Arr:
    """A simulated depth frame in metres, with missing readings written as NaN."""
    rng = np.random.default_rng(17)
    yy, xx = np.mgrid[0:rows, 0:cols].astype(float)
    d = 1.02 - 0.32 * (yy / (rows - 1))           # the table runs away from the camera
    cy, cx, rad = rows * 0.52, cols * 0.46, min(rows, cols) * 0.26
    mug = ((xx - cx) ** 2 + (yy - cy) ** 2) < rad ** 2
    d[mug] = 0.62
    d = d + rng.normal(0.0, 0.004, size=d.shape)
    gloss = ((xx - (cx - rad * 0.4)) ** 2 + (yy - (cy - rad * 0.4)) ** 2) < (rad * 0.4) ** 2
    d[gloss] = np.nan                                    # shiny: no reading comes back
    d[0, :] = np.nan                                     # beyond the sensor's near edge
    d[rows - 1, cols - 2:] = np.nan
    return np.round(d, 3)


DEPTH: Arr | None = None


def _dep() -> Arr:
    global DEPTH
    if DEPTH is None:
        DEPTH = _depth()
    return DEPTH


def depth_grid() -> None:
    d = _dep()
    miss = int(np.isnan(d).sum())
    print(f'[p3] depth frame {d.shape[0]} by {d.shape[1]}, '
          f'{d.size} readings, {miss} missing ({100 * miss / d.size:.1f} per cent)')
    print(f'[p3] nearest {np.nanmin(d):.3f} m, furthest {np.nanmax(d):.3f} m, '
          f'average of what is there {np.nanmean(d):.3f} m')
    print('[p3] first row that has readings: '
          + ' '.join('--' if np.isnan(v) else f'{v:.3f}' for v in d[1]))

    fig, ax = plt.subplots(figsize=(9.2, 7.6), facecolor='white')
    _grid_of_numbers(ax, d, fmt='{:.2f}', cmap='viridis_r', size=8.2)
    ax.text(0.0, -0.75, 'Each number is how far that pixel is, in metres. A red cell '
                        'marked -- is a pixel the camera could not measure.',
            fontsize=10.5, color=INK)
    ax.set_ylim(-1.1, d.shape[0] + 0.05)
    ax.set_title('A depth picture: one distance per pixel, and holes where the '
                 'camera got nothing back',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, STA_DOC, 'depth-grid.svg')


def depth_holes() -> None:
    d = _dep()
    zeros = np.nan_to_num(d, nan=0.0)
    honest = float(np.nanmean(d))
    wrong = float(zeros.mean())
    miss = int(np.isnan(d).sum())
    print(f'[p3] average distance counting the holes as 0 m: {wrong:.3f} m')
    print(f'[p3] average distance leaving the holes out: {honest:.3f} m')
    print(f'[p3] the hole pixels drag the answer down by '
          f'{100 * (honest - wrong) / honest:.1f} per cent')
    near = float(np.nanmin(d))
    print(f'[p3] a 0 also looks nearer than the nearest real reading, {near:.3f} m, '
          'so a safety check reads it as something touching the camera')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), facecolor='white')
    ax = axes[0]
    _plain(ax)
    vals = zeros.reshape(-1)
    ax.hist(vals[vals > 0], bins=18, color=LINK, label='real readings')
    ax.hist(vals[vals == 0], bins=[-0.02, 0.02], color=GRIP,
            label=f'the {miss} holes, written as 0')
    ax.set_xlabel('distance in metres', fontsize=10)
    ax.set_ylabel('how many pixels', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False)
    ax.set_title('A hole written as 0 lands in the middle of nothing',
                 fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    names = ['holes counted as 0 m', 'holes left out']
    ax.bar(names, [wrong, honest], color=[GRIP, SLIDE], width=0.45)
    for i, v in enumerate([wrong, honest]):
        ax.text(i, v + 0.02, f'{v:.3f} m', ha='center', fontsize=12, color=INK,
                weight='bold')
    ax.axhline(near, color=MUTED, ls='--', lw=1.2)
    ax.text(-0.46, near + 0.015, f'nearest real reading, {near:.2f} m', fontsize=9.5,
            color=MUTED, ha='left')
    ax.set_ylabel('average distance over the frame (m)', fontsize=10)
    ax.set_ylim(0, max(wrong, honest) * 1.3)
    ax.set_title('What that does to a number taken from the frame',
                 fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('A missing reading is not a distance of zero, and treating it as one '
                 'changes every answer', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'depth-holes.svg')


def _cloud() -> tuple[Arr, int, int, float]:
    """Turn a larger simulated depth frame into a list of three-number positions."""
    rows, cols = 48, 64
    d = _depth(rows, cols)
    f = 60.0                                      # focal length in pixels
    cx, cy = (cols - 1) / 2.0, (rows - 1) / 2.0
    yy, xx = np.mgrid[0:rows, 0:cols].astype(float)
    z = d
    x = (xx - cx) * z / f
    y = (yy - cy) * z / f
    ok = ~np.isnan(z)
    pts = np.column_stack([x[ok], y[ok], z[ok]])
    return pts, rows * cols, int(ok.sum()), f


def depth_to_points() -> None:
    pts, total, kept, f = _cloud()
    print(f'[p3] a {total:,}-pixel depth frame gives {kept:,} points, because '
          f'{total - kept:,} pixels had no reading')
    print(f'[p3] focal length {f:.0f} pixels; first five points (x, y, z in metres):')
    for i in range(5):
        print(f'[p3]   {pts[i, 0]:+.3f} {pts[i, 1]:+.3f} {pts[i, 2]:+.3f}')
    print(f'[p3] the list is {kept:,} x 3 = {kept * 3:,} numbers, against '
          f'{total:,} for the depth frame')

    fig = plt.figure(figsize=(12.6, 4.8), facecolor='white')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1.3], wspace=0.25)
    ax = fig.add_subplot(gs[0, 0])
    _blank(ax)
    ax.text(0.0, 6.5, 'pixel (column, row) and its distance', fontsize=10.5,
            color=MUTED)
    ax.text(0.0, 5.9, 'x = (column − centre) × distance ÷ '
                      f'{f:.0f}', fontsize=11, color=INK, family='DejaVu Sans Mono')
    ax.text(0.0, 5.3, 'y = (row − centre) × distance ÷ '
                      f'{f:.0f}', fontsize=11, color=INK, family='DejaVu Sans Mono')
    ax.text(0.0, 4.7, 'z = distance', fontsize=11, color=INK,
            family='DejaVu Sans Mono')
    head = ['x (m)', 'y (m)', 'z (m)']
    for j, h in enumerate(head):
        ax.text(1.4 + j * 1.9, 3.7, h, fontsize=10, color=MUTED, weight='bold',
                ha='center')
    for i in range(6):
        y = 3.1 - i * 0.48
        for j in range(3):
            ax.text(1.4 + j * 1.9, y, f'{pts[i, j]:+.3f}', fontsize=10, color=INK,
                    ha='center')
    ax.text(1.4, 0.0, f'... and so on, {kept:,} rows in all', fontsize=10, color=MUTED)
    ax.set_xlim(-0.2, 8.0)
    ax.set_ylim(-0.4, 7.0)
    ax.set_title('three numbers per pixel that had a reading',
                 fontsize=11.5, weight='bold', color=INK, loc='left')
    ax = fig.add_subplot(gs[0, 1])
    _plain(ax)
    sc = ax.scatter(pts[:, 0], pts[:, 2], c=pts[:, 1], cmap='viridis', s=5)
    fig.colorbar(sc, ax=ax, label='y, metres up or down from the centre', shrink=0.85)
    ax.set_xlabel('x, metres left or right (m)', fontsize=10)
    ax.set_ylabel('z, metres away from the camera (m)', fontsize=10)
    ax.set_title(f'the same {kept:,} points, seen from above',
                 fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('A depth picture becomes a point cloud: a long list of three-number '
                 'positions', fontsize=12.5, weight='bold', color=INK, y=1.03)
    _save(fig, STA_DOC, 'depth-to-points.svg')


def order_free() -> None:
    pts, _, kept, _ = _cloud()
    rng = np.random.default_rng(29)
    order = rng.permutation(len(pts))
    shuffled = pts[order]
    centre_a = pts.mean(axis=0)
    centre_b = shuffled.mean(axis=0)
    max_a = pts.max(axis=0)
    max_b = shuffled.max(axis=0)
    w = rng.normal(0, 1, size=12)
    line_a = float(pts[:4].reshape(-1) @ w)
    line_b = float(shuffled[:4].reshape(-1) @ w)
    print('[p3] average position before shuffling: '
          + ' '.join(f'{v:+.4f}' for v in centre_a))
    print('[p3] average position after shuffling:  '
          + ' '.join(f'{v:+.4f}' for v in centre_b))
    print('[p3] largest value in each column, before and after: '
          + ' '.join(f'{a:+.3f}/{b:+.3f}' for a, b in zip(max_a, max_b)))
    print(f'[p3] a layer that reads the first four rows in order gives {line_a:+.3f} '
          f'before and {line_b:+.3f} after')

    fig, ax = plt.subplots(figsize=(12.6, 5.4), facecolor='white')
    _blank(ax)
    for k, (title, arr, x0) in enumerate((('the list as the camera made it', pts, 0.0),
                                          ('the same points, shuffled', shuffled, 5.4))):
        ax.text(x0, 5.5, title, fontsize=10.5, color=INK, weight='bold')
        for j, h in enumerate(['x', 'y', 'z']):
            ax.text(x0 + 0.5 + j * 1.3, 5.0, h, fontsize=10, color=MUTED,
                    weight='bold', ha='center')
        for i in range(7):
            y = 4.4 - i * 0.52
            for j in range(3):
                ax.text(x0 + 0.5 + j * 1.3, y, f'{arr[i, j]:+.3f}', fontsize=9.6,
                        color=INK, ha='center')
        ax.text(x0, 0.45, f'... {kept:,} rows', fontsize=10, color=MUTED)
    ax.text(10.6, 5.0, 'what a network may read from the list', fontsize=10.5,
            color=INK, weight='bold')
    ax.text(10.6, 4.4, 'average of every row  (same both times)', fontsize=10,
            color=SLIDE)
    ax.text(10.6, 3.95, '  ' + '  '.join(f'{v:+.4f}' for v in centre_a), fontsize=9.6,
            color=SLIDE, family='DejaVu Sans Mono')
    ax.text(10.6, 3.5, '  ' + '  '.join(f'{v:+.4f}' for v in centre_b), fontsize=9.6,
            color=SLIDE, family='DejaVu Sans Mono')
    ax.text(10.6, 2.7, 'largest in each column  (same both times)', fontsize=10,
            color=SLIDE)
    ax.text(10.6, 2.25, '  ' + '  '.join(f'{v:+.3f}' for v in max_a), fontsize=9.6,
            color=SLIDE, family='DejaVu Sans Mono')
    ax.text(10.6, 1.8, '  ' + '  '.join(f'{v:+.3f}' for v in max_b), fontsize=9.6,
            color=SLIDE, family='DejaVu Sans Mono')
    ax.text(10.6, 1.0, 'the first four rows laid end to end,\nread by a fully '
                       'connected layer  (different)', fontsize=10, color=GRIP)
    ax.text(10.6, 0.2, f'  {line_a:+.3f}        {line_b:+.3f}', fontsize=9.6,
            color=GRIP, family='DejaVu Sans Mono')
    ax.set_xlim(-0.2, 19.0)
    ax.set_ylim(0.0, 6.0)
    ax.set_title('The order of a point cloud means nothing, so only order-blind '
                 'reading of it is safe',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, STA_DOC, 'order-free.svg')


# --------------------------------------------------------------------------
# section 4: sound
# --------------------------------------------------------------------------

RATE: int = 16_000


def _sound() -> Arr:
    """A simulated half second of a gripper closing and then touching something."""
    rng = np.random.default_rng(41)
    n = RATE // 2
    t = np.arange(n) / RATE
    motor = np.zeros(n)
    moving = t < 0.30
    for h, amp in ((1, 0.30), (2, 0.16), (3, 0.08), (5, 0.04)):
        motor[moving] += amp * np.sin(2 * np.pi * 120 * h * t[moving])
    click = np.zeros(n)
    k0 = int(0.30 * RATE)
    k = np.arange(n - k0)
    click[k0:] = 0.9 * np.exp(-k / (0.004 * RATE)) * rng.normal(0, 1, len(k))
    return motor + click + rng.normal(0, 0.01, n)


def waveform() -> None:
    s = _sound()
    t = np.arange(len(s)) / RATE
    print(f'[p4] {len(s):,} numbers for {len(s) / RATE:.2f} seconds at {RATE:,} '
          'readings a second')
    print(f'[p4] the readings run from {s.min():+.3f} to {s.max():+.3f}')
    print(f'[p4] average loudness while the motor runs {np.abs(s[:int(0.3 * RATE)]).mean():.4f}, '
          f'after the touch {np.abs(s[int(0.3 * RATE):]).mean():.4f}')

    fig, axes = plt.subplots(2, 1, figsize=(11.6, 5.6), facecolor='white',
                            gridspec_kw={'height_ratios': [1.3, 1.0]})
    ax = axes[0]
    _plain(ax)
    ax.plot(t, s, color=LINK, lw=0.5)
    ax.axvline(0.30, color=GRIP, ls='--', lw=1.3)
    ax.text(0.305, s.max() * 0.85, 'the gripper touches the mug', fontsize=10,
            color=GRIP)
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('air pressure, scaled to −1 ... +1', fontsize=10)
    ax.set_title(f'The whole half second: {len(s):,} numbers', fontsize=11.5,
                 weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    k0, k1 = int(0.100 * RATE), int(0.1125 * RATE)
    ax.plot(t[k0:k1], s[k0:k1], color=LINK, lw=1.3, marker='o', ms=2.6)
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('one reading per dot', fontsize=10)
    ax.set_title(f'{k1 - k0} of those numbers, close up: the sound is only a list of '
                 'numbers', fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('A sound arrives as a long list of readings of air pressure',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'waveform.svg')


def _stft(s: Arr, win: int = 256, hop: int = 128) -> tuple[Arr, int, int]:
    frames = 1 + (len(s) - win) // hop
    window = np.hanning(win)
    out = np.zeros((frames, win // 2 + 1))
    for i in range(frames):
        chunk = s[i * hop:i * hop + win] * window
        out[i] = np.abs(np.fft.rfft(chunk))
    return out, frames, win // 2 + 1


def spectrogram() -> None:
    s = _sound()
    mag, frames, bins = _stft(s)
    db = 20 * np.log10(mag + 1e-6)
    freqs = np.fft.rfftfreq(256, 1.0 / RATE)
    print(f'[p4] short-time Fourier transform: window 256 readings, hop 128, '
          f'{frames} frames of {bins} numbers = {frames * bins:,} numbers')
    print(f'[p4] each frame covers {256 / RATE * 1000:.1f} milliseconds and the '
          f'frames start {128 / RATE * 1000:.1f} milliseconds apart')
    print(f'[p4] the numbers run from {freqs[0]:.0f} Hz to {freqs[-1]:,.0f} Hz '
          f'in steps of {freqs[1]:.1f} Hz')

    fig, ax = plt.subplots(figsize=(11.4, 5.2), facecolor='white')
    _plain(ax)
    im = ax.imshow(db.T, origin='lower', aspect='auto', cmap='magma',
                   extent=(0, len(s) / RATE, 0, freqs[-1]))
    fig.colorbar(im, ax=ax, label='loudness of that pitch, in decibels')
    ax.axvline(0.30, color='white', ls='--', lw=1.2)
    ax.text(0.305, freqs[-1] * 0.9, 'the touch', color='white', fontsize=10)
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('pitch, in cycles a second (Hz)', fontsize=10)
    ax.set_title(f'The same sound as a grid: {frames} frames by {bins} pitches, '
                 'which a network reads like a picture',
                 fontsize=12.2, weight='bold', color=INK, loc='left')
    _save(fig, STA_DOC, 'spectrogram.svg')


def one_frame() -> None:
    s = _sound()
    mag, frames, bins = _stft(s)
    freqs = np.fft.rfftfreq(256, 1.0 / RATE)
    idx = int(0.15 * RATE) // 128
    frame = mag[idx]
    peak = int(np.argmax(frame))
    db = 20 * np.log10(frame + 1e-6)
    print(f'[p4] frame {idx} starts at {idx * 128 / RATE:.3f} seconds')
    print(f'[p4] its loudest pitch is number {peak}, which is {freqs[peak]:.0f} Hz, '
          f'at a size of {frame[peak]:.2f}')
    print(f'[p4] the raw sizes run from {frame.min():.5f} to {frame.max():.2f}, '
          f'a ratio of {frame.max() / max(frame.min(), 1e-9):,.0f} to 1')
    print(f'[p4] in decibels they run from {db.min():.1f} to {db.max():.1f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    ax.plot(freqs, frame, color=LINK, lw=1.2)
    ax.plot([freqs[peak]], [frame[peak]], 'o', color=GRIP, ms=7)
    ax.text(freqs[peak] + 300, frame[peak], f'{freqs[peak]:.0f} Hz, the motor',
            fontsize=10, color=GRIP, va='center')
    ax.set_xlabel('pitch (Hz)', fontsize=10)
    ax.set_ylabel('size of that pitch', fontsize=10)
    ax.set_title('One frame, as the arithmetic gives it', fontsize=11.5, weight='bold',
                 color=INK)
    ax = axes[1]
    _plain(ax)
    ax.plot(freqs, db, color=PURPLE, lw=1.2)
    ax.set_xlabel('pitch (Hz)', fontsize=10)
    ax.set_ylabel('size in decibels', fontsize=10)
    ax.set_title('The same frame after taking logarithms', fontsize=11.5,
                 weight='bold', color=INK)
    fig.suptitle(f'Frame {idx} of the sound, {bins} numbers: the quiet pitches only '
                 'become visible after the logarithm',
                 fontsize=12.4, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'one-frame.svg')


# --------------------------------------------------------------------------
# section 5: the robot's own readings
# --------------------------------------------------------------------------

JOINT_NAMES: list[str] = ['base', 'shoulder', 'elbow', 'wrist 1', 'wrist 2', 'wrist 3']


class Arm:
    """A simulated two second reach, recorded 100 times a second."""

    def __init__(self) -> None:
        rng = np.random.default_rng(53)
        self.hz = 100
        n = 200
        t = np.linspace(0.0, 1.0, n)
        shape = 10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5        # smooth start and stop
        start = np.array([0.00, -0.90, 1.20, -1.90, -1.57, 0.00])
        end = np.array([0.62, -0.42, 1.65, -2.40, -1.55, 0.31])
        self.angles = start + np.outer(shape, end - start)
        self.angles += rng.normal(0, 0.0002, self.angles.shape)
        self.vel = np.gradient(self.angles, 1.0 / self.hz, axis=0)
        grip = np.clip(0.085 - 0.085 * np.clip((t - 0.70) / 0.22, 0, 1), 0.0, 0.085)
        self.grip = grip + rng.normal(0, 0.0002, n)
        contact = np.clip((t - 0.80) / 0.10, 0, 1)
        self.force = np.column_stack([
            0.4 * np.sin(2 * np.pi * t) + rng.normal(0, 0.15, n),
            0.3 * np.cos(2 * np.pi * t) + rng.normal(0, 0.15, n),
            -1.0 - 11.0 * contact + rng.normal(0, 0.25, n)])
        self.t = np.linspace(0.0, 2.0, n)


ARM: Arm | None = None


def _arm() -> Arm:
    global ARM
    if ARM is None:
        ARM = Arm()
    return ARM


def joint_traces() -> None:
    a = _arm()
    print(f'[p5] {len(a.t)} readings over {a.t[-1]:.1f} seconds at {a.hz} a second')
    for i, nm in enumerate(JOINT_NAMES):
        print(f'[p5] {nm:9s} from {a.angles[0, i]:+.3f} to {a.angles[-1, i]:+.3f} '
              f'radians, fastest {np.abs(a.vel[:, i]).max():.3f} radians a second')

    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for i, nm in enumerate(JOINT_NAMES):
        ax.plot(a.t, a.angles[:, i], lw=1.8, label=nm)
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('joint angle (radians)', fontsize=10)
    ax.legend(fontsize=8.2, frameon=False, ncol=2)
    ax.set_title('six joint angles', fontsize=11.5, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    for i in range(6):
        ax.plot(a.t, a.vel[:, i], lw=1.6)
    ax.set_xlabel('seconds', fontsize=10)
    ax.set_ylabel('joint speed (radians a second)', fontsize=10)
    ax.set_title('the same six, as speeds', fontsize=11.5, weight='bold', color=INK)
    ax = axes[2]
    _plain(ax)
    ax.plot(a.t, a.grip * 1000, color=SLIDE, lw=1.8, label='gripper opening (mm)')
    ax.plot(a.t, a.force[:, 2], color=GRIP, lw=1.5, label='force down the wrist (N)')
    ax.axhline(0, color=GRID, lw=0.8)
    ax.set_xlabel('seconds', fontsize=10)
    ax.legend(fontsize=9, frameon=False, loc='center left')
    ax.set_title('gripper and wrist force', fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('Two seconds of one reach: everything the arm knows about itself, '
                 'read 100 times a second',
                 fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'joint-traces.svg')


def _state_rows(k: int) -> list[tuple[str, str, float]]:
    a = _arm()
    rows: list[tuple[str, str, float]] = []
    for i, nm in enumerate(JOINT_NAMES):
        rows.append((f'{nm} angle', 'radians', float(a.angles[k, i])))
    for i, nm in enumerate(JOINT_NAMES):
        rows.append((f'{nm} speed', 'rad/s', float(a.vel[k, i])))
    rows.append(('gripper opening', 'metres', float(a.grip[k])))
    for i, nm in enumerate(['sideways', 'forwards', 'down']):
        rows.append((f'wrist force {nm}', 'newtons', float(a.force[k, i])))
    return rows


def state_vector() -> None:
    k = 150
    rows = _state_rows(k)
    a = _arm()
    print(f'[p5] the state at {a.t[k]:.2f} seconds, {len(rows)} numbers:')
    for nm, unit, v in rows:
        print(f'[p5]   {nm:22s} {v:+9.4f} {unit}')

    fig, ax = plt.subplots(figsize=(12.6, 5.0), facecolor='white')
    _blank(ax)
    for i, (nm, unit, v) in enumerate(rows):
        col, row = divmod(i, 8)
        x = col * 4.4
        y = 7.2 - row * 0.80
        colour = (JOINT if 'angle' in nm else SLIDE if 'speed' in nm
                  else TEAL if 'gripper' in nm else GRIP)
        ax.add_patch(Rectangle((x, y), 1.55, 0.62, facecolor='white', edgecolor=colour,
                               lw=1.1))
        ax.text(x + 0.775, y + 0.31, f'{v:+.4f}', fontsize=9.6, ha='center',
                va='center', color=INK)
        ax.text(x + 1.68, y + 0.31, f'{nm}  ({unit})', fontsize=9.2, va='center',
                color=MUTED)
    ax.text(0.0, 8.15, f'the {len(rows)} numbers the arm hands the model at '
                       f'{a.t[k]:.2f} seconds, in the order the model always '
                       'expects them', fontsize=10.5, color=INK)
    ax.set_xlim(-0.2, 13.4)
    ax.set_ylim(0.3, 8.7)
    ax.set_title('Proprioception: what the arm knows about its own body, as one list '
                 'of numbers',
                 fontsize=12.5, weight='bold', color=INK, loc='left')
    _save(fig, STA_DOC, 'state-vector.svg')


def channel_ranges() -> None:
    a = _arm()
    chans: list[tuple[str, Arr, str]] = []
    for i, nm in enumerate(JOINT_NAMES):
        chans.append((f'{nm} angle', a.angles[:, i], JOINT))
    for i, nm in enumerate(JOINT_NAMES):
        chans.append((f'{nm} speed', a.vel[:, i], SLIDE))
    chans.append(('gripper opening', a.grip, TEAL))
    for i, nm in enumerate(['sideways', 'forwards', 'down']):
        chans.append((f'force {nm}', a.force[:, i], GRIP))
    spreads = [float(c[1].std()) for c in chans]
    print('[p5] spread of each channel over the two seconds:')
    for (nm, _, _), sd in zip(chans, spreads):
        print(f'[p5]   {nm:22s} {sd:.5f}')
    print(f'[p5] widest channel divided by narrowest: '
          f'{max(spreads) / min(spreads):,.0f}')

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.4), facecolor='white')
    ax = axes[0]
    _plain(ax)
    y = np.arange(len(chans))
    ax.barh(y, spreads, color=[c[2] for c in chans], height=0.68)
    for i, sd in enumerate(spreads):
        ax.text(sd * 1.15, i, f'{sd:.4f}', va='center', fontsize=8.6, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([c[0] for c in chans], fontsize=8.8)
    ax.invert_yaxis()
    ax.set_xscale('log')
    ax.set_xlim(min(spreads) * 0.4, max(spreads) * 9)
    ax.set_xlabel('spread of the channel, in its own units (log scale)', fontsize=10)
    ax.set_title(f'The widest channel moves {max(spreads) / min(spreads):,.0f} times '
                 'as far as the narrowest', fontsize=11.2, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    std = np.array(spreads)
    mean = np.array([float(c[1].mean()) for c in chans])
    norm = [(c[1] - m) / s for c, m, s in zip(chans, mean, std)]
    ax.boxplot(norm, vert=False, widths=0.6, showfliers=False)
    ax.set_yticks(range(1, len(chans) + 1))
    ax.set_yticklabels([c[0] for c in chans], fontsize=8.8)
    ax.invert_yaxis()
    ax.axvline(0, color=GRID, lw=1.0)
    ax.set_xlabel('after taking the average off and dividing by the spread',
                  fontsize=10)
    ax.set_title('After scaling, every channel asks for the same attention',
                 fontsize=11.2, weight='bold', color=INK)
    fig.suptitle('Raw robot readings are in units that have nothing to do with each '
                 'other', fontsize=12.5, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'channel-ranges.svg')


# --------------------------------------------------------------------------
# section 6: the action space
# --------------------------------------------------------------------------

L1, L2 = 0.40, 0.30


def _fk(a1: float, a2: float) -> tuple[Arr, Arr]:
    x = np.array([0.0, L1 * np.cos(a1), L1 * np.cos(a1) + L2 * np.cos(a1 + a2)])
    y = np.array([0.0, L1 * np.sin(a1), L1 * np.sin(a1) + L2 * np.sin(a1 + a2)])
    return x, y


def action_meanings() -> None:
    now = np.array([0.50, 0.70])                 # where the arm is, in radians
    out = np.array([0.10, 0.05])                 # the two numbers the model gave
    hz = 10.0
    cases = []
    cases.append(('as joint angles', *_fk(out[0], out[1])))
    cases.append(('as a change in joint angles', *_fk(now[0] + out[0], now[1] + out[1])))
    cases.append((f'as joint speeds, held for {1 / hz:.1f} s',
                  *_fk(now[0] + out[0] / hz, now[1] + out[1] / hz)))
    tip_now = _fk(*now)
    goal = np.array([tip_now[0][2] + out[0], tip_now[1][2] + out[1]])
    d = float(np.hypot(goal[0], goal[1]))
    c2 = np.clip((d ** 2 - L1 ** 2 - L2 ** 2) / (2 * L1 * L2), -1, 1)
    a2 = float(np.arccos(c2))
    a1 = float(np.arctan2(goal[1], goal[0])
               - np.arctan2(L2 * np.sin(a2), L1 + L2 * np.cos(a2)))
    cases.append(('as a change in where the hand is', *_fk(a1, a2)))
    print(f'[p6] the arm is at {now[0]:.2f} and {now[1]:.2f} radians, hand at '
          f'({tip_now[0][2]:.3f}, {tip_now[1][2]:.3f}) m')
    print(f'[p6] the model gives the two numbers {out[0]:.2f} and {out[1]:.2f}')
    for name, xs, ys in cases:
        move = float(np.hypot(xs[2] - tip_now[0][2], ys[2] - tip_now[1][2]))
        print(f'[p6] {name:34s} -> hand at ({xs[2]:+.3f}, {ys[2]:+.3f}) m, '
              f'{move * 100:.1f} cm from where it was')

    fig, axes = plt.subplots(1, 4, figsize=(13.4, 4.2), facecolor='white')
    for ax, (name, xs, ys) in zip(axes, cases):
        _plain(ax)
        ax.plot(tip_now[0], tip_now[1], color=GRID, lw=5, solid_capstyle='round',
                zorder=1)
        ax.plot(xs, ys, color=LINK, lw=4, solid_capstyle='round', zorder=2)
        ax.plot(xs, ys, 'o', color=INK, ms=5, zorder=3)
        move = float(np.hypot(xs[2] - tip_now[0][2], ys[2] - tip_now[1][2]))
        ax.plot([tip_now[0][2]], [tip_now[1][2]], 'o', color=MUTED, ms=5, zorder=3)
        ax.set_xlim(-0.25, 0.75)
        ax.set_ylim(-0.25, 0.75)
        ax.set_aspect('equal')
        ax.set_xlabel('metres', fontsize=9.5)
        ax.set_title(f'{name}\nhand moves {move * 100:.1f} cm', fontsize=10.2,
                     weight='bold', color=INK)
    fig.suptitle(f'The same two numbers, {out[0]:.2f} and {out[1]:.2f}, read four '
                 'ways: grey is where the arm was, blue is where it ends up',
                 fontsize=12.4, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'action-meanings.svg')


def absolute_vs_delta() -> None:
    a = _arm()
    absolute = a.angles
    delta = np.diff(a.angles, axis=0)
    print('[p6] joint angles as they are: average '
          + ' '.join(f'{v:+.3f}' for v in absolute.mean(0)))
    print('[p6] joint angles as they are: spread '
          + ' '.join(f'{v:.3f}' for v in absolute.std(0)))
    print('[p6] step-to-step changes: average '
          + ' '.join(f'{v:+.5f}' for v in delta.mean(0)))
    print('[p6] step-to-step changes: spread '
          + ' '.join(f'{v:.5f}' for v in delta.std(0)))
    print(f'[p6] the biggest change in one step of {1 / a.hz:.2f} s is '
          f'{np.abs(delta).max():.4f} radians')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.6), facecolor='white')
    ax = axes[0]
    _plain(ax)
    for i, nm in enumerate(JOINT_NAMES):
        ax.hist(absolute[:, i], bins=30, alpha=0.65, label=nm)
    ax.set_xlabel('joint angle (radians)', fontsize=10)
    ax.set_ylabel('how many readings', fontsize=10)
    ax.legend(fontsize=8.2, frameon=False, ncol=2)
    ax.set_title('What the model must learn to output, as absolute angles',
                 fontsize=11.2, weight='bold', color=INK)
    ax = axes[1]
    _plain(ax)
    for i in range(6):
        ax.hist(delta[:, i], bins=30, alpha=0.65)
    ax.set_xlabel('change in one step of 0.01 s (radians)', fontsize=10)
    ax.set_ylabel('how many readings', fontsize=10)
    ax.set_title('The same movement, as a change from where it already is',
                 fontsize=11.2, weight='bold', color=INK)
    fig.suptitle('Absolute angles are spread over radians; changes are all within a '
                 f'band of {np.abs(delta).max():.3f} radians',
                 fontsize=12.4, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'absolute-vs-delta.svg')


def _action_set() -> tuple[Arr, list[str]]:
    """Seven action channels: six joint changes in radians and a gripper in mm."""
    a = _arm()
    delta = np.diff(a.angles, axis=0)
    grip_mm = a.grip[1:] * 1000.0
    acts = np.column_stack([delta, grip_mm])
    names = [f'{nm} change (rad)' for nm in JOINT_NAMES] + ['gripper (mm)']
    return acts, names


def loss_dominated() -> None:
    acts, names = _action_set()
    rng = np.random.default_rng(67)
    guess = acts + rng.normal(0, 0.05 * acts.std(0), acts.shape)
    per = ((guess - acts) ** 2).mean(axis=0)
    share = 100 * per / per.sum()
    scaled_acts = (acts - acts.mean(0)) / acts.std(0)
    scaled_guess = (guess - acts.mean(0)) / acts.std(0)
    per_s = ((scaled_guess - scaled_acts) ** 2).mean(axis=0)
    share_s = 100 * per_s / per_s.sum()
    spread = acts.std(0)
    print(f'[p6] the gripper channel is {spread[-1] / spread[:6].min():,.0f} times '
          f'wider than the narrowest joint channel ({spread[-1]:.3f} mm against '
          f'{spread[:6].min():.5f} radians)')
    print('[p6] every channel is predicted equally badly, to within 5 per cent of '
          'its own spread')
    for nm, p, sh, shs in zip(names, per, share, share_s):
        print(f'[p6]   {nm:24s} squared error {p:.3e}, {sh:.2e} per cent of the '
              f'total loss; after scaling {shs:5.2f} per cent')
    print(f'[p6] the gripper channel alone is {share[-1]:.6f} per cent of the loss '
          f'before scaling and {share_s[-1]:.2f} per cent after')
    print(f'[p6] the six joint channels together are {share[:6].sum():.2e} per cent '
          'of it')

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.0), facecolor='white')
    for ax, vals, title, logx in ((axes[0], share, 'in the units the robot uses', True),
                                  (axes[1], share_s, 'after scaling every channel',
                                   False)):
        _plain(ax)
        y = np.arange(len(names))
        ax.barh(y, vals, color=[JOINT] * 6 + [TEAL], height=0.6)
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=9.2)
        ax.invert_yaxis()
        if logx:
            ax.set_xscale('log')
            ax.set_xlim(min(vals) * 0.3, 1e5)
            for i, v in enumerate(vals):
                ax.text(v * 1.6, i, f'{v:.1e}%', va='center', fontsize=9.2, color=INK)
            ax.set_xlabel('share of the total squared error (log scale)', fontsize=10)
        else:
            ax.set_xlim(0, 24)
            for i, v in enumerate(vals):
                ax.text(v + 0.5, i, f'{v:.1f}%', va='center', fontsize=9.5, color=INK)
            ax.set_xlabel('share of the total squared error', fontsize=10)
        ax.set_title(title, fontsize=11.5, weight='bold', color=INK)
    fig.suptitle('One channel measured in millimetres swallows the loss, and the six '
                 'that steer the arm are left with almost none',
                 fontsize=12.4, weight='bold', color=INK)
    fig.tight_layout()
    _save(fig, STA_DOC, 'loss-dominated.svg')


def scaled_training() -> None:
    """Train the same small network twice: on raw action units and on scaled ones."""
    a = _arm()
    acts, names = _action_set()
    state = np.column_stack([a.angles[:-1], a.vel[:-1], a.grip[:-1]])
    x = (state - state.mean(0)) / state.std(0)
    mean, std = acts.mean(0), acts.std(0)
    hidden, steps = 24, 6000

    def train(y: Arr, lr: float) -> tuple[Arr, Arr, float]:
        rng = np.random.default_rng(71)
        w1 = rng.normal(0, np.sqrt(2.0 / x.shape[1]), (x.shape[1], hidden))
        b1 = np.zeros(hidden)
        w2 = rng.normal(0, np.sqrt(2.0 / hidden), (hidden, y.shape[1]))
        b2 = np.zeros(y.shape[1])
        n = len(y)
        for _ in range(steps):
            h = np.maximum(x @ w1 + b1, 0.0)
            out = h @ w2 + b2
            d = (2.0 / n) * (out - y)
            if not np.isfinite(d).all():
                return out, np.full_like(y, np.nan), float('inf')
            gw2, gb2 = h.T @ d, d.sum(0)
            dh = (d @ w2.T) * (h > 0)
            gw1, gb1 = x.T @ dh, dh.sum(0)
            w1, b1, w2, b2 = w1 - lr * gw1, b1 - lr * gb1, w2 - lr * gw2, b2 - lr * gb2
        h = np.maximum(x @ w1 + b1, 0.0)
        out = h @ w2 + b2
        return out, out, float(np.mean((out - y) ** 2))

    grid = [10.0 ** p for p in range(-8, 1)]
    best_raw = min(((train(acts, lr)[2], lr) for lr in grid))
    best_sc = min(((train((acts - mean) / std, lr)[2], lr) for lr in grid))
    pred_raw = train(acts, best_raw[1])[0]
    pred_sc = train((acts - mean) / std, best_sc[1])[0] * std + mean
    err_raw = np.abs(pred_raw - acts).mean(0) / std
    err_sc = np.abs(pred_sc - acts).mean(0) / std
    print(f'[p6] best learning rate on raw targets {best_raw[1]:.0e} '
          f'(its own loss {best_raw[0]:.4f}); on scaled targets {best_sc[1]:.0e} '
          f'(its own loss {best_sc[0]:.4f})')
    print(f'[p6] after {steps:,} steps, average error of each channel as a share of '
          'that channel’s own spread:')
    for nm, a1, a2 in zip(names, err_raw, err_sc):
        print(f'[p6]   {nm:24s} raw targets {a1:.3f}   scaled targets {a2:.3f}')
    print(f'[p6] averaged over the six joint channels: raw {err_raw[:6].mean():.3f}, '
          f'scaled {err_sc[:6].mean():.3f}')
    print(f'[p6] the gripper channel: raw {err_raw[-1]:.3f}, scaled {err_sc[-1]:.3f}')

    fig, ax = plt.subplots(figsize=(11.6, 5.0), facecolor='white')
    _plain(ax)
    y = np.arange(len(names))
    ax.barh(y - 0.19, err_raw, height=0.36, color=GRIP, label='targets in robot units')
    ax.barh(y + 0.19, err_sc, height=0.36, color=SLIDE, label='targets scaled first')
    for i in range(len(names)):
        ax.text(err_raw[i] * 1.3, i - 0.19, f'{err_raw[i]:.2f}', va='center',
                fontsize=9, color=GRIP)
        ax.text(err_sc[i] * 1.3, i + 0.19, f'{err_sc[i]:.2f}', va='center',
                fontsize=9, color=SLIDE)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xscale('log')
    ax.set_xlim(0.01, max(err_raw.max(), err_sc.max()) * 6)
    ax.axvline(1.0, color=MUTED, ls='--', lw=1.1)
    ax.text(1.05, len(names) - 0.4, 'an error as big as the channel itself',
            fontsize=9, color=MUTED)
    ax.set_xlabel('average error, as a share of that channel’s own spread '
                  '(log scale)', fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, loc='lower right')
    ax.set_title('The same model, the same 4,000 steps: scaling the targets is what '
                 'lets the small channels be learned',
                 fontsize=12.2, weight='bold', color=INK, loc='left')
    _save(fig, STA_DOC, 'scaled-training.svg')


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
    same_tokens_different_order()
    position_vectors_added()
    rope_rotation()
    rope_relative()
    two_shadows()
    shadow_distorts()
    one_row_many_meanings()
    three_colour_grids()
    scaling_the_values()
    why_scale()
    patch_grid()
    patch_to_vector()
    patch_count_cost()
    depth_grid()
    depth_holes()
    depth_to_points()
    order_free()
    waveform()
    spectrogram()
    one_frame()
    joint_traces()
    state_vector()
    channel_ranges()
    action_meanings()
    absolute_vs_delta()
    loss_dominated()
    scaled_training()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
