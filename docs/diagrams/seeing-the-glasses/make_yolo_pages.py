"""Three pictures for the two chapters on solutions 3 and 4, which are one pair.

Solution 3 is Ultralytics YOLO26-seg exactly as it downloads. Solution 4 is the
same library, the same model and the same downloaded file with its training
continued on this cell's own pictures. Everything these pictures say is read out
of ``code/src/08_seeing-the-glasses/`` at drawing time and asserted before the
figure is written, so a picture cannot quietly go stale when a run is repeated.

    07-what-the-model-called-them.png
        Every name the borrowed model offered over the 36 pictures of
        ``what_it_named.py``, with the names its filter accepts marked. The
        whole of solution 3's failure is in this one picture: the model finds
        things and calls them frisbees.

    07-the-pair-block-by-block.png
        Found per 100 for both solutions, on spaced and on crowded
        arrangements, with every one of the five blocks of 20 held-out
        arrangements drawn as its own mark. The point is the comparison of two
        distances: the spread of either solution against the gap between them.

    08-training-holds-the-stem.png
        How much of a glass the masks covered, kind by kind, for a rule written
        by hand and for the fine-tuned model. The rule's coverage collapses on
        the two kinds with a stem and the model's does not, which is the one
        expectation about coarse outlines that the marking overturned.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_yolo_pages.py
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

from diagram_style import GLASS, GOOD, INK, LABEL_SIZE, MUTED, NOTE_SIZE, PAPER, WARN, save
from make_solution_flows_a import _audit, _figure, _note, _title, _tint
from matplotlib.patches import Rectangle

# Where the code and its results live, from this file.
CODE = Path(__file__).resolve().parents[3] / "code" / "src" / "08_seeing-the-glasses"

ZERO_SHOT = CODE / "03-yolo-zero-shot"
FINE_TUNED = CODE / "04-yolo-fine-tuned"
RULES = CODE / "01-rules-on-the-table"
AVERAGED = CODE / "results" / "results-averaged.json"

# The five blocks of 20 held-out arrangements every solution is scored on, by
# the seed each one starts at. ``run.py --from-seed`` is what wrote them.
BLOCKS = (10000, 10020, 10040, 10060, 10080)

# The four kinds, in the order these pictures want them: the two with no stem
# first, then the two with one, because the stem is what the third picture is
# about. render.KINDS in bench/render.py holds the same four.
NO_STEM = ("straight_glass", "tapered_glass")
WITH_STEM = ("stemmed_glass", "short_stemmed_glass")
READABLE = {
    "straight_glass": "straight glass",
    "tapered_glass": "tapered glass",
    "stemmed_glass": "stemmed glass",
    "short_stemmed_glass": "short stemmed glass",
}


# --------------------------------------------------------------- reading the code


def accepted_names() -> frozenset[str]:
    """The borrowed category names solution 3's filter keeps.

    Read out of ``drinking_vessels.py`` rather than copied, so that the picture
    marks whatever that file actually accepts on the day it is drawn.
    """
    source = (ZERO_SHOT / "drinking_vessels.py").read_text()
    names: list[str] = []
    for constant in ("VESSELS", "NEIGHBOURS"):
        match = re.search(rf"^{constant} = (\(.*?\))$", source, re.M)
        assert match, f"{constant} is no longer a one-line tuple in drinking_vessels.py"
        names.extend(ast.literal_eval(match.group(1)))
    return frozenset(names)


def what_it_named() -> tuple[Counter, int]:
    """Every name the model offered in ``results-names.json``, and the pictures behind it."""
    report = json.loads((ZERO_SHOT / "results-names.json").read_text())
    counted: Counter = Counter()
    for got in report["kinds"].values():
        counted.update(got["named"])
    # Three pictures per arrangement, and this many arrangements of each kind.
    pictures = report["scenes per kind"] * len(report["kinds"]) * 3
    return counted, pictures


def block(solution: Path, start: int, crowded: bool) -> dict:
    """One block's scorecard, as the solution's own run.py wrote it."""
    tail = "-crowded" if crowded else ""
    return json.loads((solution / f"results{tail}-from{start}.json").read_text())


def found_per_100(solution: Path, crowded: bool) -> list[float]:
    """Found per 100 glasses in each of the five blocks."""
    out = []
    for start in BLOCKS:
        card = block(solution, start, crowded)
        out.append(100.0 * card["find"]["found"] / card["glasses"])
    return out


def covered_by_kind(solution: Path, kind: str) -> float:
    """The mean over the five spaced blocks of how much of a glass the masks covered."""
    seen = [block(solution, start, crowded=False)["mask"]["by_kind"][kind] for start in BLOCKS]
    return sum(one["covered_median"] for one in seen) / len(seen)


# ------------------------------------------------------------------- the drawing


def _bar(axis, left: float, y: float, width: float, height: float, colour, *, pale=0.78):
    """One horizontal bar, drawn in the figure's own units."""
    patch = Rectangle(
        (left, y - height / 2.0),
        max(width, 0.0),
        height,
        facecolor=_tint(colour, pale),
        edgecolor=colour,
        linewidth=1.1,
        zorder=4,
    )
    axis.add_patch(patch)
    return patch


def _axis_line(axis, left: float, right: float, y: float, ticks, label_of, *, colour=MUTED):
    """A plain scale under a row of bars, with its ticks written under it."""
    axis.plot([left, right], [y, y], color=colour, lw=0.9, zorder=2)
    for value, where in ticks:
        axis.plot([where, where], [y, y - 0.35], color=colour, lw=0.9, zorder=2)
        axis.text(where, y - 0.6, label_of(value), ha="center", va="top",
                  fontsize=NOTE_SIZE, color=MUTED, zorder=5)


# --------------------------------------------------------------------------- #
# 1. what the borrowed model called the glasses
# --------------------------------------------------------------------------- #

def what_the_model_called_them() -> None:
    """Solution 3's whole failure, in the names it offered instead of a cup."""
    counted, pictures = what_it_named()
    kept = accepted_names()
    rows = counted.most_common()
    total = sum(counted.values())
    survived = sum(count for name, count in rows if name in kept)

    # The claim the picture makes, computed rather than written down.
    assert total == 87, total
    assert survived == 5, survived
    assert pictures == 36, pictures
    assert rows[0][0] == "frisbee" and rows[1][0] == "sports ball", rows[:2]
    assert not {name for name, _ in rows} & {"wine glass", "cup"}, rows

    left, span = 30.0, 56.0
    scale = span / rows[0][1]
    step = 2.1
    figure, axis, _aspect = _figure(10.2, 4.6 + step * len(rows) + 3.2)
    top = axis.get_ylim()[1] - 3.4

    for index, (name, count) in enumerate(rows):
        y = top - index * step
        here = name in kept
        _bar(axis, left, y, count * scale, 1.35, GOOD if here else WARN, pale=0.62 if here else 0.74)
        axis.text(left - 1.4, y, name, ha="right", va="center", fontsize=LABEL_SIZE,
                  color=INK if here else MUTED, weight="bold" if here else "normal", zorder=5)
        axis.text(left + count * scale + 1.2, y, f"{count}", ha="left", va="center",
                  fontsize=LABEL_SIZE, color=GOOD if here else WARN, weight="bold", zorder=5)

    bottom = top - (len(rows) - 1) * step
    axis.text(left + span * 0.52, top + 1.9,
              f"the filter keeps {', '.join(sorted(kept))}",
              ha="center", va="center", fontsize=NOTE_SIZE, color=INK, zorder=5,
              bbox={"boxstyle": "round,pad=0.35", "facecolor": PAPER, "edgecolor": MUTED, "lw": 0.8})

    _note(axis, 50.0, bottom - 2.9,
          f"{total} named objects over {pictures} pictures. {survived} carried a name the filter "
          "keeps.",
          colour=INK, ha="center", va="center", weight="bold", size=LABEL_SIZE)
    _note(axis, 50.0, bottom - 5.4,
          "A glass seen from straight above is a disc, and in a grey picture shaded from depth a disc "
          "has no\ntransparency, no highlight and no bright rim. The model is not lost about where the "
          "objects are.\nIt is answering a different question correctly.",
          colour=MUTED, ha="center", va="center")

    _title(axis, "What the borrowed model called the glasses")
    _audit(figure, "07-what-the-model-called-them.png")
    save(figure, "07-what-the-model-called-them.png")


# --------------------------------------------------------------------------- #
# 2. the pair, block by block
# --------------------------------------------------------------------------- #

def the_pair_block_by_block() -> None:
    """The gap the training made, against the wobble between one block and the next."""
    runs = [
        ("the borrowed model,\nas it downloads", "spaced", ZERO_SHOT, False, WARN),
        ("the borrowed model,\nas it downloads", "crowded", ZERO_SHOT, True, WARN),
        ("the same model,\nfine-tuned here", "spaced", FINE_TUNED, False, GOOD),
        ("the same model,\nfine-tuned here", "crowded", FINE_TUNED, True, GOOD),
    ]
    measured = []
    for _name, family, folder, crowded, colour in runs:
        blocks = found_per_100(folder, crowded)
        measured.append((family, blocks, sum(blocks) / len(blocks), colour))

    # Every mean has to agree with what average_blocks.py wrote, which pools the
    # glasses rather than averaging the blocks, so allow a tenth either way.
    pooled = json.loads(AVERAGED.read_text())
    crowded_pooled = json.loads(AVERAGED.with_name("results-averaged-crowded.json").read_text())
    for (_name, family, folder, crowded, _colour), (_f, blocks, mean, _c) in zip(runs, measured, strict=True):
        card = (crowded_pooled if crowded else pooled)[folder.name]
        assert abs(mean - card["found_per_100"]) < 0.15, (folder.name, family, mean, card)
        assert abs(min(blocks) - card["found_per_100_lowest"]) < 0.1, (folder.name, blocks, card)
        assert abs(max(blocks) - card["found_per_100_highest"]) < 0.1, (folder.name, blocks, card)

    # The claim: the gap between the pair is larger than either one's own spread.
    spreads = [max(blocks) - min(blocks) for _f, blocks, _m, _c in measured]
    gap_spaced = measured[2][2] - measured[0][2]
    gap_crowded = measured[3][2] - measured[1][2]
    assert min(gap_spaced, gap_crowded) > 6.0 * max(spreads), (gap_spaced, gap_crowded, spreads)
    assert min(measured[1][1]) == 0.0, measured[1][1]

    left, right = 30.0, 88.0
    numbers = right + 2.5          # one column for the means, clear of every ring
    def at(value: float) -> float:
        return left + (right - left) * value / 100.0

    step, pair_gap = 3.0, 1.6
    figure, axis, _aspect = _figure(10.4, 22.5)
    top = axis.get_ylim()[1] - 3.2

    y = top
    places = []
    for index, (family, blocks, mean, colour) in enumerate(measured):
        places.append(y)
        _bar(axis, left, y, at(mean) - left, 1.15, colour, pale=0.80)
        for value in blocks:
            axis.plot([at(value)], [y], marker="o", markersize=4.6, markerfacecolor=PAPER,
                      markeredgecolor=colour, markeredgewidth=1.3, zorder=6)
        axis.text(numbers, y, f"{mean:.1f}", ha="left", va="center", fontsize=LABEL_SIZE,
                  color=colour, weight="bold", zorder=6)
        axis.text(left - 1.4, y, family, ha="right", va="center", fontsize=LABEL_SIZE,
                  color=INK, zorder=6)
        y -= step + (pair_gap if index == 1 else 0.0)

    for index, label in ((0, "the borrowed model, as it downloads"),
                         (2, "the same model, fine-tuned here")):
        axis.text(left, places[index] + 1.9, label, ha="left", va="center",
                  fontsize=LABEL_SIZE, color=measured[index][3], weight="bold", zorder=6)

    _note(axis, at(13.0), places[1],
          "one of these five blocks of 20 arrangements found no glass at all",
          colour=WARN, ha="left", va="center", weight="bold")

    bottom = places[-1] - 2.6
    _axis_line(axis, left, right, bottom,
               [(v, at(v)) for v in (0, 25, 50, 75, 100)], lambda v: f"{v}")
    _note(axis, (left + right) / 2.0, bottom - 1.9, "glasses found per 100 put out",
          colour=INK, ha="center", va="center", size=LABEL_SIZE)

    _note(axis, 50.0, bottom - 4.2,
          "Each ring is one block of 20 held-out arrangements and each bar is the five blocks pooled. "
          "The same library,\nthe same model and the same downloaded file on both sides, with the bar "
          "on the confidence number held still,\nso the distance between the two pairs of rows is what "
          "the training bought.",
          colour=MUTED, ha="center", va="center")

    _title(axis, "What training bought, and how little the blocks disagree about it")
    _audit(figure, "07-the-pair-block-by-block.png")
    save(figure, "07-the-pair-block-by-block.png")


# --------------------------------------------------------------------------- #
# 3. the stem, which the rule loses and training does not
# --------------------------------------------------------------------------- #

def training_holds_the_stem() -> None:
    """The one expectation about coarse outlines that the marking overturned."""
    kinds = NO_STEM + WITH_STEM
    rule = {kind: covered_by_kind(RULES, kind) for kind in kinds}
    model = {kind: covered_by_kind(FINE_TUNED, kind) for kind in kinds}

    # The claim: the rule's coverage falls away on the kinds with a stem, and
    # the model's does not move.
    assert all(rule[kind] > 99.0 for kind in NO_STEM), rule
    assert all(rule[kind] < 92.0 for kind in WITH_STEM), rule
    assert all(model[kind] > 99.0 for kind in kinds), model
    assert min(model[kind] for kind in WITH_STEM) > max(rule[kind] for kind in WITH_STEM) + 9.0

    left, right = 36.0, 92.0
    def at(value: float) -> float:
        return left + (right - left) * value / 100.0

    figure, axis, _aspect = _figure(10.4, 25.6)
    top = axis.get_ylim()[1] - 2.2
    group, bar = 4.4, 1.25

    y = top
    for kind in kinds:
        axis.text(left - 1.6, y - 0.95, READABLE[kind], ha="right", va="center",
                  fontsize=LABEL_SIZE, color=INK, weight="bold" if kind in WITH_STEM else "normal",
                  zorder=6)
        for offset, (value, colour, who) in enumerate((
            (rule[kind], GLASS, "rule written by hand"),
            (model[kind], GOOD, "fine-tuned model"),
        )):
            row = y - offset * (bar + 0.55)
            _bar(axis, left, row, at(value) - left, bar, colour, pale=0.74)
            axis.text(at(value) + 1.2, row, f"{value:.1f}", ha="left", va="center",
                      fontsize=LABEL_SIZE, color=colour, weight="bold", zorder=6)
            if kind == kinds[0]:
                axis.text(left + 1.6, row, who, ha="left", va="center", fontsize=NOTE_SIZE,
                          color=INK, zorder=7)
        y -= group

    bottom = y + group - (bar + 0.55) - 2.6
    _axis_line(axis, left, right, bottom,
               [(v, at(v)) for v in (0, 25, 50, 75, 100)], lambda v: f"{v}")
    _note(axis, (left + right) / 2.0, bottom - 1.9,
          "per cent of the glass the mask covered, median over five blocks",
          colour=INK, ha="center", va="center", size=LABEL_SIZE)

    _note(axis, 50.0, bottom - 4.2,
          "Spaced arrangements, five blocks of 20. A stem is the thin part a coarse outline was "
          "expected to lose, and\nthe rule written by hand does lose it. Training the same coarse "
          "machinery on this cell's own pictures\ndoes not: all four kinds come back above 99 per cent.",
          colour=MUTED, ha="center", va="center")

    _title(axis, "The stem the written rule loses, and the trained model does not")
    _audit(figure, "08-training-holds-the-stem.png")
    save(figure, "08-training-holds-the-stem.png")


def main() -> None:
    what_the_model_called_them()
    the_pair_block_by_block()
    training_holds_the_stem()


if __name__ == "__main__":
    main()
