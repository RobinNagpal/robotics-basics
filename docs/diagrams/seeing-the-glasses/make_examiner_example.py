"""One arrangement followed from the table to the scorecard.

``03_the-examiner.md`` explains how a run is set and marked in general terms.
These six pictures do the same thing once, on one real arrangement, so that the
whole chain can be read off a single example:

    03-example-on-the-table.png         the arrangement itself, before any picture
    03-example-three-pictures.png       what the three stations each make of it
    03-example-what-one-station-gives.png  grey, depth, and the id image kept back
    03-example-the-masks.png            the mask that came back for every glass
    03-example-mask-to-record.png       one mask through the shared arithmetic
    03-example-the-scorecard.png        what this arrangement contributes

**The arrangement is the examiner's own number 10046.** It is one of the held-out
spawned arrangements, so it is what the cell's spawner really produces rather
than anything built for a diagram, and it was chosen because it shows four of
the difficulties at once: six glasses of a kind with a foot and a stem, one
glass completely covered by another at one station, a second glass partly
covered at another, and glasses cut off at the frame edge in every picture.

**Nothing here is drawn by hand.** The grey pictures, the depth readings and the
id images come from ``bench/render.py`` through ``bench/data.py``, which is the
examiner itself. The masks come from running ``01-rules-on-the-table`` on those
same pictures, so they are a solution's real output. The places, the widths and
the counts come from ``bench/masks_to_glasses.py``, ``bench/marking.py`` and
``bench/scoring.py``. Every number written on a picture is computed here by
calling that code, and none of it is typed in.

**A camera looking straight down makes a picture a plan of the table**, so every
panel is drawn in the table's own millimetres rather than in pixel rows: the
array is turned so that the table's x runs right and its y runs up. That is the
only change made to any picture, and it is what lets the pictures be read
against the plan views beside them.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_examiner_example.py

Needs matplotlib and numpy. The bench imports torch for a function none of this
calls, so an empty stand-in is put in its place when it is not installed; see
``bench_on_the_path`` below.
"""

from __future__ import annotations

import sys
import types
from functools import cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from diagram_style import (
    GLASS,
    GOOD,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    PAPER,
    TITLE_SIZE,
    WARN,
    bare,
    new,
    save,
)
from matplotlib.colors import to_rgba
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle


def bench_on_the_path() -> None:
    """Put the cell, the examiner and the first solution where ``import`` will find them.

    The examiner is three folders of plain modules rather than an installed
    package, so the folders go on the path in the order the modules expect:
    ``work_cell`` for the cell, ``bench`` for the examiner, and
    ``01-rules-on-the-table`` for the solution whose masks these pictures show.
    That folder's name begins with a digit, so it cannot be imported as a
    package and its modules are imported as top-level ones, which is how the
    solution's own ``run.py`` imports them too.

    ``bench/pictures.py`` imports torch for one function that turns a picture
    into a tensor. Nothing here calls it, and torch is not in the environment
    these diagrams run in, so an empty module stands in for it. Shading a
    picture into greys, which these diagrams do use, is plain numpy.
    """
    root = Path(__file__).resolve().parents[3] / "code" / "src" / "08_seeing-the-glasses"
    for folder in ("work_cell", "bench", "01-rules-on-the-table"):
        sys.path.insert(0, str(root / folder))
    try:
        import torch  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["torch"] = types.ModuleType("torch")


bench_on_the_path()

import data  # noqa: E402
import find  # noqa: E402
import marking  # noqa: E402
import masks_to_glasses  # noqa: E402
import pictures  # noqa: E402
import render  # noqa: E402
from scoring import MERGED_SHARE, Scorecard  # noqa: E402
from work_cell.arm.dimensions import SURVEY_HEIGHT  # noqa: E402
from work_cell.glasses.shapes import KIND_RANGES  # noqa: E402
from work_cell.glasses.spawn import MIN_SEPARATION  # noqa: E402
from work_cell.rack.layout import GLASS_ZONE  # noqa: E402
from work_cell.table.layout import TABLE_TOP_Z  # noqa: E402

# Which arrangement these pictures follow, and which of its stations is shown in
# full. The middle station is the one that holds all six glasses, so it is the
# one picture in which every glass has a mask to show.
SEED = 10046
STATION = 1

# The glass whose mask is followed through the shared arithmetic. It is the one
# standing nearest the point below the camera, so the station sees it squarest
# and the arithmetic has its best chance; what is left over is the floor of the
# step rather than the fault of the mask.
FOLLOWED = 4

FAINT = "#eef1f4"

# Millimetres of table one pixel covers at the table top, from the cell's own
# survey height and its own lens.
PIXEL_MM = 1000.0 * SURVEY_HEIGHT / render.FOCAL

# The glass zone in millimetres, as (x from, x to, y from, y to).
ZONE = tuple(1000.0 * v for v in GLASS_ZONE)


def tint(fraction: float) -> tuple[float, float, float, float]:
    """``GLASS`` mixed with white, for an id image that has to show six glasses."""
    base, white = np.array(to_rgba(GLASS)), np.ones(4)
    return tuple(white + (base - white) * fraction)


ID_TINTS = [tint(f) for f in (0.26, 0.44, 0.62, 0.80, 0.98, 0.35)]


# --------------------------------------------------------------------------- #
# the arrangement, the pictures, and what the solution and the examiner make of them
# --------------------------------------------------------------------------- #


@cache
def example():
    """Arrangement ``SEED``, with the picture from every station. The examiner's own."""
    return data.spawned(SEED)


@cache
def kind_words() -> str:
    """The kind of glass on the table, in words rather than in a module's spelling."""
    return example().kind.replace("_", " ")


def glasses():
    return example().glasses


def sight(index: int = STATION):
    return example().sights[index]


def station_mm(index: int) -> np.ndarray:
    """Where a station's camera stands, in millimetres, as the cell works it out."""
    return 1000.0 * np.asarray(data.under(example().sights[index].pose))


def glass_mm(index: int) -> np.ndarray:
    """Where glass ``index`` really stands, in millimetres. One based, as the ids are."""
    glass = glasses()[index - 1]
    return np.array([1000.0 * glass.x, 1000.0 * glass.y])


def height_mm(index: int) -> float:
    return 1000.0 * glasses()[index - 1].total_height


def rim_mm(index: int) -> float:
    return 2000.0 * float(glasses()[index - 1].radius[-1])


def keys() -> list[int]:
    """The glasses by number, the way the id image numbers them."""
    return list(range(1, len(glasses()) + 1))


@cache
def reports(index: int = STATION):
    """What the solution returns for one station's picture, each matched to a glass.

    Matched the examiner's way: the pixels of the report are carried into the one
    picture that holds every glass, and the glass that owns most of them is the
    glass the report is about. That is ``scoring.Scorecard.found``'s rule, used
    here one report at a time so that each can be drawn beside the glass it
    turned out to be.
    """
    seen = sight(index)
    found, doubts = find.load().find(seen.picture, example().kind)
    matched = {}
    for one in found:
        carried = data.in_reference(seen.picture, one.pixels, example().reference)
        ids = example().reference.ids[carried[:, 0], carried[:, 1]]
        owned = ids[ids > 0]
        if owned.size == 0:
            continue
        counts = np.bincount(owned)
        matched[int(counts.argmax())] = (one, float(counts.max() / owned.size))
    return matched, doubts


def mask_of(one, shape=None) -> np.ndarray:
    """One report's pixels as a boolean picture, the shape scoring.mask counts them in."""
    shape = shape or sight().picture.depth.shape
    mask = np.zeros(shape, dtype=bool)
    mask[one.pixels[:, 0], one.pixels[:, 1]] = True
    return mask


def mask_numbers(one, key: int, index: int = STATION) -> tuple[float, float]:
    """How much of the glass the mask covered, and how much of it was not the glass.

    ``scoring.Scorecard.mask``'s own arithmetic, in percentages: the truth is
    what that station could see of that glass, which is its part of the id image.
    """
    truth = example().sights[index].visible[key - 1]
    here = np.unique(one.pixels, axis=0)
    on_it = int(np.count_nonzero(truth[here[:, 0], here[:, 1]]))
    whole = int(np.count_nonzero(truth))
    return 100.0 * on_it / whole, 100.0 * (len(here) - on_it) / len(here)


def standing(key: int, index: int) -> tuple[str, int, int]:
    """How one station holds one glass: whole, cut off at the frame edge, or not at all.

    Three numbers decide it, all read off the renderer. ``visible`` is the pixels
    of that glass the camera can see. ``whole`` is where that glass alone would
    have landed, so the difference between them is what another glass stands in
    front of. A mask that reaches the border of the picture is cut off, which is
    ``masks_to_glasses.cut_off``'s own question.
    """
    seen = example().sights[index]
    visible = seen.visible[key - 1]
    count = int(np.count_nonzero(visible))
    covered = int(np.count_nonzero(seen.whole[key - 1] & ~visible))
    if count == 0:
        return "gone", count, covered
    return ("cut" if masks_to_glasses.cut_off(visible) else "whole"), count, covered


def covered_by(key: int, index: int) -> int:
    """Which glass takes the pixels of ``key`` that ``index``'s picture has not got."""
    seen = example().sights[index]
    ids = seen.picture.ids[seen.whole[key - 1] & ~seen.visible[key - 1]]
    taken = ids[ids > 0]
    return int(np.bincount(taken).argmax()) if taken.size else 0


@cache
def survey():
    """The whole run of this arrangement through the examiner, and its scorecard.

    ``marking.survey`` asks the solution about each station's picture and brings
    the three answers together, keeping for each place the report from the
    station that saw the glass squarest. ``marking.score`` then marks what is
    left. This is the same pair of calls every solution's ``run.py`` makes.
    """
    card = Scorecard()
    kept, station = marking.survey(find.load(), example(), card)
    marking.score(card, example(), kept, station)
    which = {id(seen): number for number, seen in enumerate(example().sights, start=1)}
    rows = []
    for one in kept:
        seen = station[id(one)]
        carried = data.in_reference(seen.picture, one.pixels, example().reference)
        ids = example().reference.ids[carried[:, 0], carried[:, 1]]
        owned = ids[ids > 0]
        counts = np.bincount(owned)
        key = int(counts.argmax())
        shares = np.sort(counts[counts > 0])[::-1] / owned.size
        place = np.array([1000.0 * one.x, 1000.0 * one.y])
        rows.append({
            "key": key,
            "station": which[id(seen)],
            "place": place,
            "error": float(np.linalg.norm(place - glass_mm(key))),
            "width": 1000.0 * one.width,
            "pixels": len(one.pixels),
            "cut_off": one.cut_off,
            "best_share": float(shares[0]),
            "second_share": float(shares[1]) if shares.size > 1 else 0.0,
            "covered": mask_numbers(one, key, which[id(seen)] - 1)[0],
            "not_the_glass": mask_numbers(one, key, which[id(seen)] - 1)[1],
        })
    rows.sort(key=lambda row: row["key"])
    return card, rows


def exact_mask_place(key: int, index: int):
    """Where the examiner's own id mask of one glass puts it, through the same step.

    The floor of the step: the best place that arithmetic can give, since the
    mask it is given is exactly right. Comparing a solution's place against this
    says whether an error belongs to the mask or to the view.
    """
    seen = example().sights[index]
    one = masks_to_glasses.one_glass(seen.picture, seen.visible[key - 1])
    if one is None:
        return None
    return np.array([1000.0 * one.x, 1000.0 * one.y]), 1000.0 * one.width


# --------------------------------------------------------------------------- #
# a picture as a plan of the table
# --------------------------------------------------------------------------- #
#
# The survey cameras look straight down, so a picture is the table seen from
# above and scaled. The renderer's rows run along falling x and its columns along
# falling y, which would print every picture rotated a quarter turn and mirrored
# against the plan views beside it. Turning the array once, here, is what keeps
# the two readable together.


def as_plan(array: np.ndarray) -> np.ndarray:
    """A picture turned so that the table's x runs right and its y runs up."""
    return array[::-1, ::-1].T


def as_plan_colour(array: np.ndarray) -> np.ndarray:
    """The same turn, for a picture that carries a colour at every pixel."""
    return np.stack([as_plan(array[..., band]) for band in range(array.shape[-1])], axis=-1)


def plan_extent(index: int) -> tuple[float, float, float, float]:
    """Where a station's picture sits on the table, in millimetres, as imshow wants it."""
    rows, columns = sight(index).picture.depth.shape
    across, down = render.LENS.cy, render.LENS.cx
    x, y = station_mm(index)
    return (x - (rows - 1 - across + 0.5) * PIXEL_MM, x + (across + 0.5) * PIXEL_MM,
            y - (columns - 1 - down + 0.5) * PIXEL_MM, y + (down + 0.5) * PIXEL_MM)


def plan_axes(index: int) -> tuple[np.ndarray, np.ndarray]:
    """The table coordinate of every pixel centre, for drawing a line on a picture.

    Indexed the way ``as_plan`` leaves a picture: the first array runs along the
    table's x and the second along its y, both rising.
    """
    rows, columns = sight(index).picture.depth.shape
    x, y = station_mm(index)
    return (x + (np.arange(rows) - (rows - 1 - render.LENS.cy)) * PIXEL_MM,
            y + (np.arange(columns) - (columns - 1 - render.LENS.cx)) * PIXEL_MM)


def pixel_to_table(index: int, rows, columns) -> tuple[float, float]:
    """Where a pixel of a station's picture sits on the table, in millimetres.

    The renderer's rows run along falling x and its columns along falling y, so
    this is the one place that conversion is written down. Everything that needs
    to put a label on a picture goes through it rather than through the arrays
    ``plan_axes`` returns, which are indexed the other way round.
    """
    x, y = station_mm(index)
    return (x - (np.mean(rows) - render.LENS.cy) * PIXEL_MM,
            y - (np.mean(columns) - render.LENS.cx) * PIXEL_MM)


def show_grey(axis, index: int) -> None:
    """The grey picture a solution is handed, as the examiner shades it.

    ``pictures.shade`` is the examiner's own shading, written once so that every
    solution is handed the same bytes, and this is its one grey channel.
    """
    axis.imshow(as_plan(pictures.grey(example().sights[index].picture)), cmap="gray",
                vmin=0, vmax=255, origin="lower", extent=plan_extent(index),
                interpolation="nearest", zorder=1)


def outline(axis, index: int, mask: np.ndarray, colour: str, width: float = 1.6,
            style="solid") -> None:
    """The boundary of one mask, drawn on a plan of the table."""
    xs, ys = plan_axes(index)
    axis.contour(xs, ys, as_plan(mask).astype(float), levels=[0.5], colors=[colour],
                 linewidths=width, linestyles=[style], zorder=6)


def frame_patch(axis, index: int, colour=INK) -> Rectangle:
    """The edge of one station's picture, which is what cuts a glass off."""
    x0, x1, y0, y1 = plan_extent(index)
    patch = Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor=colour,
                      linestyle=(0, (5, 3)), linewidth=1.2, zorder=7)
    axis.add_patch(patch)
    return patch


# --------------------------------------------------------------------------- #
# drawing helpers
# --------------------------------------------------------------------------- #


def titles(figure, axes, labels, colours=None, *, heading=None, lift=0.02) -> None:
    """Panel titles on one line, whatever the panels' shapes do to their boxes.

    ``set_title`` hangs a title off the axes box, and an equal-aspect plan view
    has a shorter box than the panel beside it, so two titles set that way come
    out at different heights. The same helper, for the same reason, as the other
    scripts in this folder.
    """
    figure.canvas.draw()
    boxes = [axis.get_position() for axis in axes]
    top = max(box.y1 for box in boxes)
    colours = colours or [INK] * len(labels)
    for box, label, colour in zip(boxes, labels, colours, strict=True):
        figure.text((box.x0 + box.x1) / 2.0, top + lift, label, ha="center", va="bottom",
                    fontsize=TITLE_SIZE, color=colour)
    if heading:
        figure.text(0.5, top + lift + 0.062, heading, ha="center", va="bottom",
                    fontsize=TITLE_SIZE + 1, color=INK)


def under(figure, axes, texts, colours=None, *, y=0.10) -> None:
    """A block of sentences under each panel, set in figure coordinates.

    Text this long does not fit inside a picture without landing on a glass, and
    a white box over the picture hides the thing being described.
    """
    figure.canvas.draw()
    colours = colours or [INK] * len(texts)
    for axis, text, colour in zip(axes, texts, colours, strict=True):
        box = axis.get_position()
        figure.text((box.x0 + box.x1) / 2.0, y, text, ha="center", va="top",
                    fontsize=NOTE_SIZE, color=colour)


def note(axis, x, y, text, *, colour=INK, ha="left", va="top", size=NOTE_SIZE, alpha=0.9):
    """A block of text that stays readable over a shaded picture."""
    return axis.text(x, y, text, ha=ha, va=va, color=colour, fontsize=size, zorder=14,
                     bbox={"facecolor": "white", "edgecolor": "none", "alpha": alpha, "pad": 2.4})


def pointer(axis, text, at, to, *, colour=WARN, ha="left", va="top"):
    """A sentence set clear of the drawing, with a line to what it is about."""
    axis.annotate(text, xy=at, xytext=to, fontsize=NOTE_SIZE, color=colour, ha=ha, va=va,
                  zorder=15, arrowprops={"arrowstyle": "->", "color": colour, "linewidth": 1.1},
                  bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 2.4})


def caption(figure, text, *, y=0.012) -> None:
    figure.text(0.5, y, text, ha="center", va="bottom", fontsize=NOTE_SIZE, color=MUTED)


def text_panel(axis) -> None:
    """A panel that holds sentences rather than a drawing."""
    bare(axis)
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.0)


def zone_patch(axis, *, fill=True, colour=MUTED) -> None:
    """The glass zone, as the cell's layout file gives it.

    Never labelled on the drawing. The zone is where the glasses are, so every
    spot a label could go is a spot a glass may stand in; what the rectangle is
    is said in the words beside the picture instead.
    """
    x0, x1, y0, y1 = ZONE
    axis.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=FAINT if fill else "none",
                             edgecolor=colour, linestyle=":", linewidth=1.2, zorder=2))


def footprint(axis, key: int, *, colour=GLASS, alpha=0.30, number=True, zorder=8) -> None:
    """Where one glass really stands, as the circle its rim covers on the table.

    The number goes inside the circle rather than above it. Above it, the number
    of a glass standing at the edge of the zone lands on the dotted line that
    draws the zone, and a line through a digit is harder to read than a digit on
    a pale disc.
    """
    centre, radius = glass_mm(key), rim_mm(key) / 2.0
    axis.add_patch(Circle(centre, radius, facecolor=colour, alpha=alpha, edgecolor=colour,
                          linewidth=1.1, zorder=zorder))
    axis.plot(*centre, marker="+", ms=5, mew=1.2, color=INK, zorder=zorder + 1)
    if number:
        axis.text(centre[0], centre[1] + radius * 0.46, str(key), ha="center", va="center",
                  fontsize=LABEL_SIZE, color=INK, fontweight="bold", zorder=zorder + 2)


def rows_of_text(axis, x, y, rows, *, step=0.052, size=NOTE_SIZE, colour=INK) -> float:
    """Several lines down a text panel, returning where the next one would go."""
    for row in rows:
        axis.text(x, y, row, ha="left", va="top", fontsize=size, color=colour)
        y -= step
    return y


def listed(numbers) -> str:
    """``[2, 3, 4]`` as "2, 3 and 4", because a picture is read as a sentence."""
    numbers = [str(n) for n in numbers]
    if not numbers:
        return "none"
    if len(numbers) == 1:
        return numbers[0]
    return ", ".join(numbers[:-1]) + " and " + numbers[-1]


# --------------------------------------------------------------------------- #
# 1. the arrangement on the table
# --------------------------------------------------------------------------- #


def on_the_table() -> None:
    """The ground truth: where the examiner put the glasses, before any picture.

    Everything the other five pictures say is measured against this, so it is
    drawn first and drawn plainly: the circle each glass covers on the table, the
    zone the glasses stand in, and the three places the camera stands.
    """
    figure, axes = plt.subplots(1, 2, figsize=(12.4, 7.0),
                               gridspec_kw={"width_ratios": [1.3, 1.0]})
    figure.patch.set_facecolor(PAPER)
    plan, told = axes
    figure.subplots_adjust(left=0.04, right=0.98, top=0.86, bottom=0.08, wspace=0.04)
    for axis in axes:
        axis.set_facecolor(PAPER)

    bare(plan)
    plan.set_aspect("equal")
    plan.set_xlim(252.0, 712.0)
    plan.set_ylim(-478.0, -38.0)
    zone_patch(plan)
    for key in keys():
        footprint(plan, key)

    for number in range(len(example().sights)):
        place = station_mm(number)
        plan.plot(*place, marker="o", ms=7, color=INK, zorder=10)
        plan.text(place[0] + 11.0, place[1], f"station {number + 1}", ha="left", va="center",
                  fontsize=NOTE_SIZE, color=INK, zorder=11)
    first, last = station_mm(0), station_mm(len(example().sights) - 1)
    plan.plot([first[0], last[0]], [first[1], last[1]], color=INK, linewidth=1.0,
              linestyle=(0, (2, 2)), zorder=9)

    # ---- what the examiner knows about this arrangement
    text_panel(told)
    y = rows_of_text(told, 0.0, 0.985, [
        f"The examiner drew this arrangement from the number {SEED}, which is one",
        f"of the numbers held back for testing. It holds {len(glasses())} glasses, and every",
        f"one of them is a {kind_words()}: an arrangement holds four to six",
        "glasses of a single kind, and the kind changes from one arrangement",
        "to the next.",
    ], step=0.040)

    gap = station_mm(1)[1] - station_mm(0)[1]
    y = rows_of_text(told, 0.0, y - 0.022, [
        f"The dotted rectangle is the glass zone, {ZONE[1] - ZONE[0]:.0f} mm across by "
        f"{ZONE[3] - ZONE[2]:.0f} mm deep,",
        "which is the part of the table glasses are put on. The three dots",
        f"are where the camera stands to photograph it: {gap:.0f} mm apart, all of",
        f"them {1000 * SURVEY_HEIGHT:.0f} mm above the table and all looking straight down.",
    ], step=0.040)

    low, high = KIND_RANGES[example().kind]["height"]
    narrow, wide = KIND_RANGES[example().kind]["bowl_diameter"]
    tallest, shortest = max(map(height_mm, keys())), min(map(height_mm, keys()))
    y = rows_of_text(told, 0.0, y - 0.022, [
        f"A {kind_words()} may be {1000 * low:.0f} to {1000 * high:.0f} mm tall with a bowl "
        f"{1000 * narrow:.0f} to {1000 * wide:.0f} mm",
        f"across. These six run from {shortest:.0f} to {tallest:.0f} mm tall. The table below gives",
        "each glass the number the id image gives it, which is the number",
        "used in every picture that follows; read across it for how tall",
        "that glass is, how wide its rim is, and where it stands.",
    ], step=0.040)

    columns = (0.02, 0.17, 0.37, 0.56)
    y -= 0.022
    for label, x in zip(("glass", "height", "rim across", "stands at"), columns, strict=True):
        told.text(x, y, label, ha="left", va="top", fontsize=NOTE_SIZE, color=MUTED)
    y -= 0.042
    for key in keys():
        place = glass_mm(key)
        cells = (str(key), f"{height_mm(key):.0f} mm", f"{rim_mm(key):.0f} mm",
                 f"x = {place[0]:.0f} mm, y = {place[1]:.0f} mm")
        for cell, x in zip(cells, columns, strict=True):
            told.text(x, y, cell, ha="left", va="top", fontsize=NOTE_SIZE, color=INK)
        y -= 0.042

    apart = min(float(np.linalg.norm(glass_mm(a) - glass_mm(b)))
                for a in keys() for b in keys() if a < b)
    rows_of_text(told, 0.0, y - 0.018, [
        f"No two centres may come closer than {1000 * MIN_SEPARATION:.0f} mm. The closest pair here",
        f"stands {apart:.0f} mm apart, so no glass touches another.",
    ], step=0.040)

    titles(figure, axes, ["Where the glasses stand", "What the examiner put out"],
           heading=f"One arrangement, number {SEED}: "
                   f"{len(glasses())} {kind_words()}es on the table", lift=0.015)
    caption(figure,
            "Seen from straight above. Each shaded circle is the part of the table one glass covers, and the "
            "cross at its middle is where it stands.\nNo picture has been taken yet: this is what the examiner "
            "knows, and what everything reported later is marked against.")
    save(figure, "03-example-on-the-table.png")


# --------------------------------------------------------------------------- #
# 2. the three pictures the three stations produce
# --------------------------------------------------------------------------- #


def three_pictures() -> None:
    """The same arrangement from the three stations, side by side.

    The three panels share one set of limits, so the frame sliding along y from
    one station to the next can be seen, and so can what that sliding does: a
    glass whole in one picture is cut off in another, and one glass is in no
    pixel of the first picture at all because a taller glass's bowl is thrown out
    over it.
    """
    figure, axes = new(13.6, 9.0, columns=len(example().sights))
    figure.subplots_adjust(left=0.03, right=0.99, top=0.89, bottom=0.19, wspace=0.06)

    frames = [plan_extent(number) for number in range(len(example().sights))]
    x0 = min(frame[0] for frame in frames) - 10.0
    x1 = max(frame[1] for frame in frames) + 10.0
    y0 = min(frame[2] for frame in frames) - 10.0
    y1 = max(frame[3] for frame in frames) + 10.0

    held = []
    for number, axis in enumerate(axes):
        bare(axis)
        axis.set_aspect("equal")
        axis.set_xlim(x0, x1)
        axis.set_ylim(y0, y1)
        show_grey(axis, number)
        frame_patch(axis, number)
        # Over a picture whose table is nearly black, the grey the plan views use
        # for the zone and the ink they use for the station cannot be seen, so
        # both are drawn pale here.
        zone_patch(axis, fill=False, colour="#c3cad2")
        axis.plot(*station_mm(number), marker="o", ms=6, mfc="white", mec=INK, mew=1.2, zorder=10)

        whole, cut, gone = [], [], []
        for key in keys():
            how, _, _ = standing(key, number)
            {"whole": whole, "cut": cut, "gone": gone}[how].append(key)
            colour = {"whole": GOOD, "cut": WARN, "gone": MUTED}[how]
            place = glass_mm(key)
            if how == "gone":
                axis.plot(*place, marker="+", ms=8, mew=1.6, color=colour, zorder=9)
                continue
            outline(axis, number, example().sights[number].visible[key - 1], colour)
            # Opaque, because a glass standing at the edge of the zone has the
            # dotted zone line or the dashed frame edge running behind its
            # number, and a line through a digit is hard to read.
            note(axis, place[0], place[1], str(key), colour=colour, ha="center", va="center",
                 size=LABEL_SIZE, alpha=1.0)
        held.append((whole, cut, gone))

    # ---- the two things this arrangement does that a list of counts would hide
    hidden = [key for key in keys() if standing(key, 0)[0] == "gone"]
    if hidden:
        key = hidden[0]
        behind = covered_by(key, 0)
        lost = standing(key, 0)[2]
        pointer(axes[0], f"glass {key} is in no pixel of this picture.\n"
                         f"Its outline falls inside the frame, but\nall {lost} of those pixels show glass "
                         f"{behind},\nwhose bowl is thrown out over it.",
                glass_mm(key), (x0 + 14.0, y1 - 14.0), colour=WARN, ha="left", va="top")

    # The glass another glass stands partly in front of at the last station. The
    # arrow is aimed a little below that glass's own number, so that it ends on
    # the picture rather than on the digit.
    partly = max(keys(), key=lambda key: standing(key, 2)[2])
    aim = glass_mm(partly) + np.array([0.0, -26.0])
    axes[2].annotate("", xy=aim, xytext=(x0 + 150.0, y0 + 136.0),
                     arrowprops={"arrowstyle": "->", "color": WARN, "linewidth": 1.1}, zorder=15)
    note(axes[2], x0 + 14.0, y0 + 134.0,
         f"glass {partly} keeps {standing(partly, 2)[1]} pixels here and\nloses "
         f"{standing(partly, 2)[2]} of them to glass {covered_by(partly, 2)}",
         colour=WARN, ha="left", va="top")

    names, notes, colours = [], [], []
    for number, (whole, cut, gone) in enumerate(held):
        names.append(f"Station {number + 1}, at y = {station_mm(number)[1]:.0f} mm")
        notes.append(f"whole in the picture: {listed(whole)}\n"
                     f"cut off at the frame edge: {listed(cut)}\n"
                     f"not in this picture at all: {listed(gone)}")
        colours.append(INK)
    titles(figure, axes, names, heading="The three pictures the three stations make of that one "
                                        "arrangement", lift=0.012)
    under(figure, axes, notes, colours, y=0.145)
    caption(figure,
            "The dashed rectangle is the edge of each station's picture, the dot is the point on the table below "
            "its camera, and the dotted rectangle is the glass zone. The glasses keep the numbers they have on the "
            "table. A green outline is a glass the picture holds whole, a red one a glass cut off where the picture "
            "ends.\nThese outlines are the examiner's own id image and not a solution's answer: this is what is "
            "really there to be found.", y=0.015)
    save(figure, "03-example-three-pictures.png")


# --------------------------------------------------------------------------- #
# 3. what one station hands over, and what it keeps
# --------------------------------------------------------------------------- #


def what_one_station_gives() -> None:
    """One station's picture in full: the grey, the depth, and the id image.

    The first two go to the solution with the camera's pose. The third is
    rendered beside them and never handed over, which is what makes marking
    possible at all.
    """
    picture = sight().picture
    figure, axes = new(13.2, 6.0, columns=3)
    figure.subplots_adjust(left=0.03, right=0.97, top=0.84, bottom=0.20, wspace=0.14)
    grey_axis, depth_axis, id_axis = axes
    extent = plan_extent(STATION)

    show_grey(grey_axis, STATION)
    depth = np.ma.masked_invalid(as_plan(1000.0 * picture.depth))
    drawn = depth_axis.imshow(depth, cmap="Blues", origin="lower", extent=extent,
                             interpolation="nearest")
    bar = figure.colorbar(drawn, ax=depth_axis, fraction=0.045, pad=0.03)
    bar.set_label("millimetres along the camera's view axis", fontsize=NOTE_SIZE, color=INK)
    bar.ax.tick_params(labelsize=NOTE_SIZE - 0.8, colors=INK)
    bar.outline.set_visible(False)

    shown = np.zeros(picture.ids.shape + (4,), dtype=float)
    shown[...] = to_rgba(FAINT)
    for order, key in enumerate(keys()):
        shown[picture.ids == key] = ID_TINTS[order % len(ID_TINTS)]
    id_axis.imshow(as_plan_colour(shown), origin="lower", extent=extent, interpolation="nearest")
    for key in keys():
        there = np.argwhere(picture.ids == key)
        if not there.size:
            continue
        x, y = pixel_to_table(STATION, there[:, 0], there[:, 1])
        id_axis.text(x, y, str(key), ha="center", va="center", fontsize=LABEL_SIZE, color=INK,
                     fontweight="bold", zorder=9)

    for axis in axes:
        bare(axis)
        axis.set_aspect("equal")
        axis.set_xlim(extent[0], extent[1])
        axis.set_ylim(extent[2], extent[3])

    place = station_mm(STATION)
    nothing = 100.0 * np.count_nonzero(picture.ids == 0) / picture.ids.size
    under(figure, axes, [
        f"{render.WIDTH} by {render.HEIGHT} pixels, one shade per pixel, bright\n"
        "where the surface is near the lens. Shaded by the\nexaminer, so all six solutions are handed the "
        "same bytes.",
        f"The nearest rim reads {1000 * picture.depth.min():.0f} mm below the camera and\n"
        f"the bare table {1000 * picture.depth[np.isfinite(picture.depth)].max():.0f} mm. Handed over with the "
        f"camera's pose:\nx = {place[0]:.0f} mm, y = {place[1]:.0f} mm, "
        f"{1000 * SURVEY_HEIGHT:.0f} mm up, looking straight down.",
        f"At each pixel, which glass it shows, or nothing: "
        f"{nothing:.0f} per\ncent of this picture is table. Rendered beside the other\n"
        "two and never handed to a solution while it answers.",
    ], [GOOD, GOOD, WARN], y=0.165)
    titles(figure, axes, ["The grey picture", "The depth reading at every pixel",
                          "The id image, which it keeps"], [GOOD, GOOD, WARN],
           heading=f"What station {STATION + 1} gives a solution, and what it keeps back", lift=0.012)
    caption(figure,
            "One station, one arrangement, three renders of it. The two green panels and the pose are the whole "
            "input: a solution is handed them rather\nthan fetching them, so none of the six can quietly read the "
            "third one.")
    save(figure, "03-example-what-one-station-gives.png")


# --------------------------------------------------------------------------- #
# 4. the mask that came back for every glass
# --------------------------------------------------------------------------- #


def mask_window() -> tuple[float, float]:
    """One window size, large enough for every glass's mask and truth at this station.

    The same size for all six panels, because the point of putting them side by
    side is that a mask covering a quarter of its glass looks different from one
    covering nearly all of it, and panels cropped tight to their own contents
    would hide exactly that.
    """
    matched, _ = reports()
    across, down = 0.0, 0.0
    for key, (one, _) in matched.items():
        both = mask_of(one) | sight().visible[key - 1]
        rows, columns = np.nonzero(both)
        across = max(across, (rows.max() - rows.min() + 1) * PIXEL_MM)
        down = max(down, (columns.max() - columns.min() + 1) * PIXEL_MM)
    return across + 34.0, down + 34.0


def the_masks() -> None:
    """One panel per glass: the mask the solution handed back, over the glass itself.

    Six panels rather than a sample of them, because the two numbers the examiner
    takes off a mask run from nearly all of the glass down to a quarter of it in
    this one picture, and which glass is which is the whole explanation.
    """
    matched, doubts = reports()
    window = mask_window()
    figure, axes = plt.subplots(2, 3, figsize=(12.8, 9.4))
    figure.patch.set_facecolor(PAPER)
    figure.subplots_adjust(left=0.03, right=0.98, top=0.86, bottom=0.14,
                          wspace=0.08, hspace=0.40)
    extent = plan_extent(STATION)

    for key, axis in zip(keys(), axes.ravel(), strict=True):
        axis.set_facecolor(PAPER)
        bare(axis)
        axis.set_aspect("equal")
        one, _ = matched[key]
        mine, truth = mask_of(one), sight().visible[key - 1]

        shown = np.zeros(truth.shape + (4,), dtype=float)
        shown[...] = (0.0, 0.0, 0.0, 0.0)
        shown[truth & mine] = to_rgba(GLASS, 0.52)
        shown[truth & ~mine] = to_rgba(WARN, 0.62)
        shown[mine & ~truth] = to_rgba(GOOD, 0.62)
        show_grey(axis, STATION)
        axis.imshow(as_plan_colour(shown), origin="lower", extent=extent,
                    interpolation="nearest", zorder=4)
        outline(axis, STATION, mine, INK, width=1.0)

        rows, columns = np.nonzero(truth | mine)
        middle = pixel_to_table(STATION, rows, columns)
        axis.set_xlim(middle[0] - window[0] / 2.0, middle[0] + window[0] / 2.0)
        axis.set_ylim(middle[1] - window[1] / 2.0, middle[1] + window[1] / 2.0)

        covered, not_the_glass = mask_numbers(one, key)
        axis.set_title(f"glass {key}", fontsize=TITLE_SIZE, color=INK, pad=5.0)
        axis.text(0.5, -0.02,
                  f"covered {covered:.1f} per cent of the glass\n"
                  f"{not_the_glass:.1f} per cent of the mask was not the glass\n"
                  f"{len(one.pixels)} pixels, "
                  + ("cut off at the frame edge" if one.cut_off else "whole in the picture"),
                  transform=axis.transAxes, ha="center", va="top", fontsize=NOTE_SIZE, color=INK)

    worst = min(matched, key=lambda key: mask_numbers(matched[key][0], key)[0])
    best = max(matched, key=lambda key: mask_numbers(matched[key][0], key)[0])
    seen_best = int(np.count_nonzero(sight().visible[best - 1]))
    seen_worst = int(np.count_nonzero(sight().visible[worst - 1]))
    figure.text(0.5, 0.935,
                f"Every mask here lost the band at the base of its glass and the foot under it, which is where a "
                f"written rule stops being sure. What that costs depends on how much of the\nglass the station "
                f"sees: glass {best}, almost under the camera, keeps "
                f"{mask_numbers(matched[best][0], best)[0]:.1f} per cent of the {seen_best} pixels station "
                f"{STATION + 1} sees of it, while glass {worst}, at the far edge of the\npicture, keeps "
                f"{mask_numbers(matched[worst][0], worst)[0]:.1f} per cent of {seen_worst}. Not one of the six "
                "masks claimed a pixel that was not its glass, so the right-hand number is zero six times over.",
                ha="center", va="top", fontsize=NOTE_SIZE, color=INK)
    figure.text(0.5, 0.985, f"The mask that came back for every glass, in station {STATION + 1}'s picture",
                ha="center", va="top", fontsize=TITLE_SIZE + 1, color=INK)

    swatches = ((to_rgba(GLASS, 0.52), "the glass, and in the mask"),
                (to_rgba(WARN, 0.62), "the glass, and not in the mask"),
                (to_rgba(GOOD, 0.62), "in the mask, and not the glass"))
    for index, (colour, label) in enumerate(swatches):
        x = 0.11 + index * 0.29
        figure.patches.append(Rectangle((x, 0.052), 0.012, 0.015, facecolor=colour,
                                        edgecolor=MUTED, linewidth=0.6,
                                        transform=figure.transFigure, figure=figure))
        figure.text(x + 0.018, 0.0595, label, ha="left", va="center", fontsize=NOTE_SIZE, color=INK)
    caption(figure,
            f"These masks are the real output of 01-rules-on-the-table, run on station {STATION + 1}'s grey picture "
            f"and depth reading and told only that the glasses are {kind_words()}es. It returned "
            f"{len(matched)} masks and "
            + ("no doubts" if not doubts else f"{len(doubts)} doubts") +
            ". Each is drawn over what that station can really see of its glass.", y=0.008)
    save(figure, "03-example-the-masks.png")


# --------------------------------------------------------------------------- #
# 5. one mask through the examiner's shared arithmetic
# --------------------------------------------------------------------------- #


def the_chain(key: int = FOLLOWED):
    """``masks_to_glasses.one_glass`` walked a step at a time, on one real mask.

    Returns what each step holds, so the picture can draw the same numbers the
    examiner computes: the points the mask's pixels become, which of them are at
    the top of the glass, the axis their middle gives, how far the cloud reaches
    from that axis, and the record that comes out.
    """
    one, _ = reports()[0][key]
    picture = sight().picture
    points = render.to_world(picture, one.pixels[:, 0], one.pixels[:, 1])
    usable = np.isfinite(points).all(1)
    points = points[usable]
    heights = 1000.0 * (points[:, 2] - TABLE_TOP_Z)
    band = points[:, 2] >= points[:, 2].max() - masks_to_glasses.RIM_BAND
    axis = 1000.0 * points[band][:, :2].mean(0)
    reach = 1000.0 * np.linalg.norm(points[:, :2] - points[band][:, :2].mean(0), axis=1)
    cut = float(np.percentile(reach, masks_to_glasses.SPREAD))
    return {
        "report": one,
        "xy": 1000.0 * points[:, :2],
        "heights": heights,
        "band": band,
        "axis": axis,
        "reach": reach,
        "cut": cut,
        "width": 2.0 * cut,
        "place": np.array([1000.0 * one.x, 1000.0 * one.y]),
    }


def mask_to_record() -> None:
    """One mask followed into the record it becomes, with the truth beside it.

    The glass followed is the one standing nearest the point below the camera, so
    nothing about the view is working against the arithmetic. What error is left
    is therefore the floor of this step, which the last panel shows by running
    the examiner's own exact mask of the same glass through the same arithmetic.
    """
    key = FOLLOWED
    chain = the_chain(key)
    one = chain["report"]
    truth = glass_mm(key)
    figure, axes = new(14.6, 6.0, columns=4)
    figure.subplots_adjust(left=0.03, right=0.99, top=0.86, bottom=0.27, wspace=0.14)
    mask_axis, cloud_axis, axis_axis, record_axis = axes

    # ---- the mask, over the picture it was drawn in
    bare(mask_axis)
    mask_axis.set_aspect("equal")
    show_grey(mask_axis, STATION)
    outline(mask_axis, STATION, mask_of(one), WARN, width=1.8)

    # The first panel and the last three are not the same view, and the window
    # has to be worked out twice because of it. The mask is where the glass
    # landed in the picture, and seen from above a bowl lands well away from the
    # foot it stands on. The points are where the depth readings put that same
    # glass back in the room, which is around the foot. So the mask's window
    # comes from the pixels and the others' from the points, and both are
    # stretched to hold the place the glass really stands.
    def window_round(xs, ys, pad=14.0):
        span_x = (min(xs.min(), truth[0]), max(xs.max(), truth[0]))
        span_y = (min(ys.min(), truth[1]), max(ys.max(), truth[1]))
        centre = np.array([sum(span_x) / 2.0, sum(span_y) / 2.0])
        return centre, max(span_x[1] - span_x[0], span_y[1] - span_y[0]) / 2.0 + pad

    rows, columns = one.pixels[:, 0], one.pixels[:, 1]
    seen_centre, seen_half = window_round(
        np.array([pixel_to_table(STATION, rows.min(), 0)[0], pixel_to_table(STATION, rows.max(), 0)[0]]),
        np.array([pixel_to_table(STATION, 0, columns.min())[1],
                  pixel_to_table(STATION, 0, columns.max())[1]]))
    mask_axis.set_xlim(seen_centre[0] - seen_half, seen_centre[0] + seen_half)
    mask_axis.set_ylim(seen_centre[1] - seen_half, seen_centre[1] + seen_half)
    mask_axis.plot(*truth, marker="+", ms=9, mew=1.6, color=GOOD, zorder=9)

    middle, half = window_round(chain["xy"][:, 0], chain["xy"][:, 1])
    axis_axis.set_xlim(middle[0] - half, middle[0] + half)
    axis_axis.set_ylim(middle[1] - half, middle[1] + half)

    # ---- every pixel of it as a point in the room, seen edge on
    #
    # Edge on rather than from above, because from above a stemmed glass is its
    # own bowl and nearly every point is at the same height, which is a panel of
    # one colour. From the side the points stand up off the table, the band the
    # axis is taken from is a slab across the top, and the next panel then says
    # where that slab sits on the table.
    bare(cloud_axis)
    cloud_axis.set_aspect("equal")
    cloud_axis.scatter(chain["xy"][:, 0], chain["heights"], c=GLASS, s=1.2, linewidths=0.0,
                      zorder=4)
    top = float(chain["heights"].max())
    band_mm = 1000.0 * masks_to_glasses.RIM_BAND
    left, right = middle[0] - half, middle[0] + half
    cloud_axis.set_xlim(left, right)
    cloud_axis.set_ylim(-26.0, top + 70.0)
    cloud_axis.plot([left, right], [0.0, 0.0], color=INK, linewidth=1.4, zorder=5)
    cloud_axis.text(right - 4.0, -4.0, "the table top", ha="right", va="top",
                   fontsize=NOTE_SIZE, color=INK)
    cloud_axis.add_patch(Rectangle((left, top - band_mm), right - left, band_mm,
                                   facecolor=to_rgba(WARN, 0.20), edgecolor=WARN,
                                   linewidth=0.9, zorder=6))
    note(cloud_axis, middle[0], top + 10.0,
         f"the top {band_mm:.0f} mm of the cloud,\nwhich is where the axis comes from",
         colour=WARN, ha="center", va="bottom")

    # ---- the points at the top of the glass, their middle, and how far the cloud reaches
    bare(axis_axis)
    axis_axis.set_aspect("equal")
    axis_axis.scatter(chain["xy"][~chain["band"], 0], chain["xy"][~chain["band"], 1],
                     c=MUTED, s=1.2, linewidths=0.0, zorder=3)
    axis_axis.scatter(chain["xy"][chain["band"], 0], chain["xy"][chain["band"], 1],
                     c=WARN, s=2.2, linewidths=0.0, zorder=4)
    axis_axis.add_patch(Circle(chain["axis"], chain["cut"], facecolor="none", edgecolor=GLASS,
                               linewidth=1.4, linestyle=(0, (5, 3)), zorder=6))
    axis_axis.plot(*chain["axis"], marker="x", ms=10, mew=2.0, color=INK, zorder=8)
    reach_to = chain["axis"] + np.array([0.0, -chain["cut"]])
    axis_axis.add_patch(FancyArrowPatch(chain["axis"], reach_to, arrowstyle="-|>",
                                        mutation_scale=9, color=GLASS, linewidth=1.2,
                                        shrinkA=0, shrinkB=0, zorder=7))
    note(axis_axis, chain["axis"][0] + 8.0, chain["axis"][1] - chain["cut"] / 2.0,
         f"{chain['cut']:.1f} mm", colour=GLASS, ha="left", va="center", alpha=1.0)

    # ---- the record, against where the glass really stands
    bare(record_axis)
    record_axis.set_aspect("equal")
    close = max(chain["width"], rim_mm(key)) / 2.0 + 20.0
    record_axis.set_xlim(truth[0] - close, truth[0] + close)
    record_axis.set_ylim(truth[1] - close, truth[1] + close)
    record_axis.add_patch(Circle(truth, rim_mm(key) / 2.0, facecolor=to_rgba(GOOD, 0.16),
                                 edgecolor=GOOD, linewidth=1.3, zorder=3))
    record_axis.add_patch(Circle(chain["place"], chain["width"] / 2.0, facecolor="none",
                                 edgecolor=WARN, linewidth=1.4, linestyle=(0, (5, 3)), zorder=4))
    record_axis.plot(*truth, marker="+", ms=11, mew=2.0, color=GOOD, zorder=8)
    record_axis.plot(*chain["place"], marker="x", ms=11, mew=2.0, color=WARN, zorder=8)
    error = float(np.linalg.norm(chain["place"] - truth))
    note(record_axis, truth[0], truth[1] + 9.0, f"{error:.1f} mm apart", colour=INK,
         ha="center", va="bottom", alpha=1.0)
    note(record_axis, truth[0], truth[1] - close + 4.0,
         f"the reported place, and a width of {chain['width']:.1f} mm",
         colour=WARN, ha="center", va="bottom", alpha=0.95)
    note(record_axis, truth[0], truth[1] + close - 4.0,
         f"where the glass stands, and its {rim_mm(key):.1f} mm rim",
         colour=GOOD, ha="center", va="top", alpha=0.95)

    exact = exact_mask_place(key, STATION)
    floor = float(np.linalg.norm(exact[0] - truth))
    apart = float(np.linalg.norm(exact[0] - chain["place"]))
    under(figure, axes, [
        f"The mask 01-rules-on-the-table returned for glass {key},\n"
        f"{len(one.pixels)} pixels of station {STATION + 1}'s picture. The green cross\n"
        "is where the glass really stands.",
        "Each of those pixels carries a depth reading, so it is a\n"
        f"point in the room. Seen edge on they are nearly all rim:\n"
        f"the highest reads {top:.0f} mm above the table, the lowest "
        f"{chain['heights'].min():.0f} mm.",
        f"The {int(np.count_nonzero(chain['band']))} points in that top band are drawn red, and\n"
        "their middle is the axis. The cloud reaches "
        f"{chain['cut']:.1f} mm\nfrom the axis at the "
        f"{masks_to_glasses.SPREAD}th percentile of all its points.",
        f"Place x = {chain['place'][0]:.1f} mm, y = {chain['place'][1]:.1f} mm, "
        f"width {chain['width']:.1f} mm,\nagainst a true place of x = {truth[0]:.1f} mm, "
        f"y = {truth[1]:.1f} mm\nand a rim {rim_mm(key):.1f} mm across.",
    ], y=0.225)

    titles(figure, axes, ["The mask", "Its pixels as points in the room",
                          "The top of the glass, and the reach", "The record it becomes"],
           heading="One mask through the examiner's own arithmetic, which is the same for "
                   "all six solutions", lift=0.012)
    caption(figure,
            f"The axis is taken from the top of the glass and not from the whole cloud, because a rim seen from "
            f"above leans away from the point below the camera. Handed the examiner's own exact mask of glass "
            f"{key} instead, the same arithmetic puts it {floor:.1f} mm out, which is {apart:.1f} mm from where "
            f"this mask put it:\nthe error left here belongs to the step and to the view rather than to the mask. "
            f"The width is a rough one by design, and it is {chain['width'] - rim_mm(key):+.1f} mm against the "
            "rim.")
    save(figure, "03-example-mask-to-record.png")


# --------------------------------------------------------------------------- #
# 6. what this arrangement contributes to the scorecard
# --------------------------------------------------------------------------- #


def the_scorecard() -> None:
    """The eight numbers this one arrangement adds, each traced back to a glass.

    The survey is three pictures, so the examiner keeps one report per place and
    takes the one from the station that saw the glass squarest. That is why the
    station named beside a report here is not always the station whose masks the
    pictures above show.
    """
    card, rows = survey()
    counts = card.count
    figure, axes = plt.subplots(1, 2, figsize=(13.8, 8.2),
                               gridspec_kw={"width_ratios": [1.0, 1.15]})
    figure.patch.set_facecolor(PAPER)
    figure.subplots_adjust(left=0.03, right=0.98, top=0.87, bottom=0.11, wspace=0.05)
    plan, card_axis = axes
    for axis in axes:
        axis.set_facecolor(PAPER)

    bare(plan)
    plan.set_aspect("equal")
    plan.set_xlim(262.0, 702.0)
    plan.set_ylim(-478.0, -38.0)
    zone_patch(plan)
    for key in keys():
        footprint(plan, key)
    for row in rows:
        truth = glass_mm(row["key"])
        plan.plot(*row["place"], marker="x", ms=9, mew=1.8, color=WARN, zorder=11)
        plan.add_patch(FancyArrowPatch(truth, row["place"], arrowstyle="-", color=WARN,
                                       linewidth=1.3, shrinkA=0, shrinkB=0, zorder=10))

    # ---- the scorecard itself
    text_panel(card_axis)
    y = 0.985
    card_axis.text(0.0, y, "The five counts", ha="left", va="top", fontsize=TITLE_SIZE, color=INK)
    y -= 0.046
    second = 100.0 * max(row["second_share"] for row in rows)
    reasons = {
        "found": ["one report per glass, each kept from the station that saw that glass squarest"],
        "missed": ["every glass got a report: what one station loses, another holds"],
        "merged": [f"no report had a second glass owning more than {100 * MERGED_SHARE:.0f} per cent of its "
                   "pixels. The most",
                   f"any second glass owned was {second:.0f} per cent"],
        "split": ["no glass collected two reports once the three stations were brought together"],
        "false": ["every report's pixels belonged to a glass"],
    }
    for name in ("found", "missed", "merged", "split", "false"):
        colour = GOOD if (name == "found") == bool(counts[name]) else WARN
        card_axis.text(0.0, y, f"{counts[name]}", ha="left", va="top", fontsize=TITLE_SIZE,
                       color=colour, fontweight="bold")
        card_axis.text(0.05, y, name, ha="left", va="top", fontsize=NOTE_SIZE, color=colour)
        rows_of_text(card_axis, 0.05, y - 0.026, reasons[name], step=0.028, colour=MUTED)
        y -= 0.032 + 0.028 * len(reasons[name])

    # ---- every number above, against the report it came from
    y -= 0.010
    card_axis.text(0.0, y, "The six reports, one per glass", ha="left", va="top",
                   fontsize=TITLE_SIZE, color=INK)
    y -= 0.046
    columns = (0.0, 0.10, 0.27, 0.46, 0.70)
    headings = ("glass", "station", "place out by", "mask covered", "pixels")
    for heading, x in zip(headings, columns, strict=True):
        card_axis.text(x, y, heading, ha="left", va="top", fontsize=NOTE_SIZE, color=MUTED)
    y -= 0.036
    for row in rows:
        cells = (str(row["key"]), str(row["station"]), f"{row['error']:.1f} mm",
                 f"{row['covered']:.1f} per cent", f"{row['pixels']}")
        for cell, x in zip(cells, columns, strict=True):
            card_axis.text(x, y, cell, ha="left", va="top", fontsize=NOTE_SIZE, color=INK)
        y -= 0.034

    worst_place = max(rows, key=lambda row: row["error"])
    median_place = float(np.median([row["error"] for row in rows]))
    quality = card.mask_quality()["all"]
    worst_mask = min(rows, key=lambda row: row["covered"])
    gaps = []
    for row in rows:
        exact = exact_mask_place(row["key"], row["station"] - 1)
        if exact is not None:
            gaps.append(float(np.linalg.norm(exact[0] - row["place"])))
    y -= 0.020
    card_axis.text(0.0, y, "What those six add up to", ha="left", va="top",
                   fontsize=TITLE_SIZE, color=INK)
    rows_of_text(card_axis, 0.0, y - 0.046, [
        f"The place is {median_place:.1f} mm out in the middle, and at worst {worst_place['error']:.1f} mm on "
        f"glass {worst_place['key']}, whose mask at station",
        f"{worst_place['station']} "
        + ("was cut off at the frame edge and held" if worst_place["cut_off"] else "held")
        + f" only {worst_place['pixels']} pixels. Handed the examiner's own exact masks,",
        f"the same arithmetic puts these six within {max(gaps):.1f} mm of the same places, so almost none of",
        "that error belongs to the masks.",
        "",
        f"The masks covered {quality['covered_median']} per cent of their glass in the middle, "
        f"{quality['covered_worst']} per cent at worst. None of them claimed",
        f"a pixel that was not its glass, so the second mask number is {quality['not_the_glass_worst']} per "
        "cent even at worst.",
    ], step=0.030)

    titles(figure, axes, ["The six reports against the six glasses", "What this arrangement adds"],
           heading=f"What arrangement {SEED} contributes to the scorecard", lift=0.015)
    caption(figure,
            f"Each cross is where a report put a glass and each plus is where that glass stands, joined by the "
            f"distance between them. Every one of them comes from one survey of three pictures, and the "
            f"station named is the one the examiner kept, which is the station the glass stood nearest the camera "
            f"of.\nThe masks behind these numbers are 01-rules-on-the-table's, and the counts, the place error and "
            "the two mask numbers are bench/scoring.py's own.")
    save(figure, "03-example-the-scorecard.png")


def main() -> None:
    on_the_table()
    three_pictures()
    what_one_station_gives()
    the_masks()
    mask_to_record()
    the_scorecard()


if __name__ == "__main__":
    main()
