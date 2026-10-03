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
            out.append(f'if the {o} is on the {p} then {v} the {o} {ex}')
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


def main() -> None:
    """Draw every picture. Pass --png <folder> to also write PNG copies for checking."""
    global PNG_DIR
    if len(sys.argv) == 3 and sys.argv[1] == '--png':
        PNG_DIR = pathlib.Path(sys.argv[2])
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    report_text_machinery()
    print(f'wrote the diagrams under {IMAGES}')


if __name__ == '__main__':
    main()
