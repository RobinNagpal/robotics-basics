"""Draw the diagrams that belong to the question of where the camera may stand.

These are different in kind from the other generators in this folder. Those
plot what the cell's own functions return, so they cannot drift from the code.
These are drawn from the geometry written in the documents beside them, so the
numbers in the two places have to be kept in step by hand.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_problem_images.py

Needs matplotlib.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402

AREA = "seeing-the-glasses"
IMAGES = Path(__file__).resolve().parents[2] / "images" / AREA
FOLDERS = json.loads((Path(__file__).parent / "image_folders.json").read_text())

INK = "#22272e"
MUTED = "#8b949e"
GLASS = "#4c8fd6"
WARN = "#d9694b"
GOOD = "#5aa469"
PAPER = "#ffffff"


def _new(width: float, height: float):
    figure, axes = plt.subplots(figsize=(width, height))
    figure.patch.set_facecolor(PAPER)
    axes.set_facecolor(PAPER)
    return figure, axes


def _save(figure, name: str) -> None:
    """Write a picture into the folder of every document that shows it."""
    folders = FOLDERS.get(name)
    if not folders:
        raise SystemExit(
            f"{name} is in no document, so image_folders.json does not say "
            "where it goes. Add the name and its document folder there first."
        )
    for folder in folders:
        out = IMAGES / folder
        out.mkdir(parents=True, exist_ok=True)
        figure.savefig(out / name, dpi=150, bbox_inches="tight", facecolor=PAPER)
        print(f"wrote docs/images/{AREA}/{folder}/{name}")
    plt.close(figure)


def _bare(axes) -> None:
    axes.set_xticks([])
    axes.set_yticks([])
    for side in axes.spines.values():
        side.set_visible(False)




# ------------------------------------------------------------- problem 2


def problem_2_where_can_the_camera_stand() -> None:
    """Which side of a glass the camera may be put, once there are several.

    Problem 1 could stand anywhere. Here each other glass casts a wedge the
    camera may not be in, and the arm's reach cuts off the rest.
    """
    figure, axes = _new(6.6, 6.0)
    _bare(axes)
    axes.set_xlim(-0.05, 1.05)
    axes.set_ylim(-0.05, 1.05)
    axes.set_aspect("equal")

    base = (0.5, -0.02)
    target = (0.50, 0.52)
    others = [(0.24, 0.62), (0.72, 0.66), (0.58, 0.30)]
    radius = 0.045

    # the band of reach
    for r, label in ((0.34, None), (0.82, "the arm's comfortable reach")):
        axes.add_patch(Circle(base, r, fill=False, ec=MUTED, lw=1.0, ls=(0, (5, 4))))
        if label:
            axes.text(0.5, base[1] + r + 0.02, label, ha="center", fontsize=8.2, color=MUTED)

    # a wedge behind each other glass: the camera may not look through it
    import math as _math

    for other in others:
        dx, dy = other[0] - target[0], other[1] - target[1]
        span = _math.hypot(dx, dy)
        middle = _math.degrees(_math.atan2(dy, dx))
        half = _math.degrees(_math.asin(min(1.0, (radius * 2.2) / span)))
        wedge = plt.matplotlib.patches.Wedge(
            target, 0.46, middle - half, middle + half, fc=WARN, alpha=0.16, ec="none"
        )
        axes.add_patch(wedge)

    for other in others:
        axes.add_patch(Circle(other, radius, fc=MUTED, alpha=0.5, ec=MUTED))
    axes.add_patch(Circle(target, radius, fc=GLASS, alpha=0.75, ec=GLASS, lw=1.6))
    axes.text(
        target[0] + 0.055, target[1] + 0.055, "the glass to measure",
        ha="left", fontsize=8.6, color=GLASS,
    )

    # two camera positions: one that works, one that does not
    good_at = (0.50 - 0.30, 0.52 - 0.05)
    bad_at = (0.50 + 0.26, 0.52 - 0.28)
    axes.plot(*good_at, marker="s", ms=8, color=GOOD)
    axes.text(
        good_at[0] - 0.02, good_at[1] + 0.055, "reachable, and\nnothing behind",
        ha="center", fontsize=8.2, color=GOOD,
    )
    axes.plot([good_at[0], target[0]], [good_at[1], target[1]], color=GOOD, lw=1.3)

    axes.plot(*bad_at, marker="s", ms=8, color=WARN)
    axes.text(
        bad_at[0] + 0.055, bad_at[1] - 0.005, "another glass\nin the frame",
        ha="left", va="center", fontsize=8.2, color=WARN,
    )
    axes.plot([bad_at[0], target[0]], [bad_at[1], target[1]], color=WARN, lw=1.3, ls=(0, (4, 3)))

    axes.plot(*base, marker="^", ms=10, color=INK)
    axes.text(base[0], base[1] - 0.045, "arm base", ha="center", fontsize=8.4, color=INK)

    axes.set_title(
        "Where the camera may stand, once there are several glasses",
        fontsize=11.5, color=INK, pad=12,
    )
    _save(figure, "where-can-the-camera-stand.png")


def main() -> None:
    problem_2_where_can_the_camera_stand()


if __name__ == "__main__":
    main()
