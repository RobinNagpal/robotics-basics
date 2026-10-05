"""Draw the diagrams that belong to the statement of the pushing problem.

These are different in kind from the other generators in this folder. Those
plot what the cell's own functions return, so they cannot drift from the code.
These are drawn from the geometry written in the documents beside them, so the
numbers in the two places have to be kept in step by hand.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_problem_images.py

Needs matplotlib.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402

AREA = "pushing-the-glasses-apart"
IMAGES = Path(__file__).resolve().parents[2] / "images" / AREA
FOLDERS = json.loads((Path(__file__).parent / "image_folders.json").read_text())

INK = "#22272e"
MUTED = "#8b949e"
GLASS = "#4c8fd6"
WARN = "#d9694b"
GOOD = "#5aa469"
PAPER = "#ffffff"

# The room a two-finger gripper needs round a glass, as a radius from the
# glass's middle: half the open jaw, plus the finger, plus a little. Kept here
# beside the picture it is drawn in, and stated in the problem statement of
# this book, docs/09_pushing-the-glasses-apart/01_the-problem/01_what-is-asked-for.md.
CLEARANCE_MM = 70.0
GLASS_MM = 75.0


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




def problem_3_the_room_a_gripper_needs() -> None:
    """Why two glasses that are not touching can still be un-grippable.

    The gap that matters is not between the glasses. It is between one glass
    and everything the gripper has to put somewhere.
    """
    figure, (before, after) = plt.subplots(1, 2, figsize=(10.6, 4.6))
    figure.patch.set_facecolor(PAPER)

    scale = 1.0 / 400.0  # millimetres to axis units

    def draw(axis, centres, title, ok):
        _bare(axis)
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
        axis.set_aspect("equal")
        axis.set_title(title, fontsize=10.5, color=INK, pad=8)
        for cx, cy in centres:
            axis.add_patch(
                Circle(
                    (cx, cy), (CLEARANCE_MM * scale), fill=False,
                    ec=GOOD if ok else WARN, lw=1.3, ls=(0, (4, 3)),
                )
            )
            axis.add_patch(
                Circle((cx, cy), (GLASS_MM / 2) * scale, fc=GLASS, alpha=0.6, ec=GLASS, lw=1.4)
            )
        # the jaw, drawn round the left glass
        cx, cy = centres[0]
        jaw, pad = 14 * scale, (GLASS_MM / 2 + 4) * scale
        for left_edge in (cx - pad - jaw, cx + pad):
            axis.add_patch(
                Rectangle(
                    (left_edge, cy - 22 * scale), jaw, 44 * scale,
                    fc=INK, alpha=0.75, ec="none",
                )
            )
        axis.text(
            centres[0][0], centres[0][1] + (CLEARANCE_MM + 16) * scale,
            f"{CLEARANCE_MM:.0f} mm of room needed",
            ha="center", fontsize=8.4, color=GOOD if ok else WARN,
        )
        gap = (centres[1][0] - centres[0][0]) / scale
        axis.annotate(
            "", xy=(centres[0][0], 0.18), xytext=(centres[1][0], 0.18),
            arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2),
        )
        axis.text(
            (centres[0][0] + centres[1][0]) / 2, 0.135,
            f"{gap:.0f} mm apart", ha="center", fontsize=8.6, color=INK,
        )

    draw(
        before, [(0.36, 0.55), (0.36 + 105 * scale, 0.55)],
        "before: the jaw has nowhere to go", False,
    )
    draw(
        after, [(0.30, 0.55), (0.30 + 160 * scale, 0.55)],
        "after: a 55 mm drag is enough", True,
    )

    after.add_patch(
        FancyArrowPatch(
            (0.30 + 105 * scale, 0.42), (0.30 + 160 * scale, 0.42),
            arrowstyle="-|>", mutation_scale=12, color=WARN, lw=1.6,
        )
    )
    after.text(0.30 + 132 * scale, 0.345, "drag", ha="center", fontsize=8.4, color=WARN)

    figure.suptitle(
        "The gap that matters is the one the gripper has to fit in",
        fontsize=12, color=INK, y=1.0,
    )
    figure.tight_layout()
    _save(figure, "the-room-a-gripper-needs.png")




def problem_3_push_low_or_it_topples() -> None:
    """Where on a glass it may be pushed, and what decides it.

    A pushed object slides if the contact is below a/mu and tips above it,
    where a is half the base width and mu is the friction with the table. The
    number depends on the glass, so it is worked out per glass.
    """
    figure, axes = _new(9.8, 4.4)
    _bare(axes)
    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1)

    def glass(x0, topples):
        colour = WARN if topples else GOOD
        # a tapered glass, side on
        body = [(x0, 0.22), (x0 - 0.005, 0.74), (x0 + 0.105, 0.74), (x0 + 0.10, 0.22)]
        axes.add_patch(plt.Polygon(body, closed=False, fill=False, ec=GLASS, lw=2.0))
        axes.plot([x0, x0 + 0.10], [0.22, 0.22], color=GLASS, lw=2.0)
        return colour

    axes.plot([0.04, 0.96], [0.22, 0.22], color=INK, lw=1.6)
    axes.text(0.50, 0.16, "the table", ha="center", fontsize=8.4, color=MUTED)

    # left: pushed low, it slides
    glass(0.14, topples=False)
    axes.add_patch(
        FancyArrowPatch((0.075, 0.30), (0.135, 0.30), arrowstyle="-|>",
                        mutation_scale=14, color=GOOD, lw=2.0)
    )
    axes.text(0.19, 0.30, "pushed low: it slides", fontsize=9, color=GOOD, va="center")
    axes.annotate("", xy=(0.125, 0.22), xytext=(0.125, 0.30),
                  arrowprops=dict(arrowstyle="<->", color=GOOD, lw=1.0))
    axes.text(0.115, 0.26, "h", ha="right", va="center", fontsize=9, color=GOOD)

    # right: pushed high, it tips
    glass(0.60, topples=True)
    axes.add_patch(
        FancyArrowPatch((0.535, 0.64), (0.595, 0.64), arrowstyle="-|>",
                        mutation_scale=14, color=WARN, lw=2.0)
    )
    axes.text(0.72, 0.64, "pushed high: it tips", fontsize=9, color=WARN, va="center")
    axes.add_patch(
        FancyArrowPatch((0.70, 0.30), (0.745, 0.365), arrowstyle="-|>",
                        mutation_scale=11, color=WARN, lw=1.4,
                        connectionstyle="arc3,rad=0.4")
    )
    axes.plot([0.70], [0.22], marker="o", ms=5, color=WARN)
    axes.text(0.705, 0.185, "tips about this edge", fontsize=8, color=WARN)

    axes.text(
        0.50, 0.90,
        "it slides while   h  <  a / \u03bc"
        "      (a = half the base width,  \u03bc = friction with the table)",
        ha="center", fontsize=10, color=INK,
    )
    axes.text(
        0.50, 0.83,
        "a wide foot at the slippery end of the range leaves room above anything the gripper\n"
        "can reach; a narrow foot at the grippy end leaves less — and that glass is refused",
        ha="center", fontsize=8.4, color=MUTED,
    )

    figure.suptitle(
        "How low the push has to be is a property of the glass",
        fontsize=12, color=INK, y=1.04,
    )
    _save(figure, "push-low-or-it-topples.png")




# ----------------------------------------- problem 2, the solution overview


def _two_glasses(axis, near=(0.38, 0.30), far=(0.58, 0.45), r=0.10):
    """The same two overlapping silhouettes, for the three-answers panel."""
    for centre, alpha in ((far, 0.30), (near, 0.55)):
        axis.add_patch(
            plt.Polygon(
                [
                    (centre[0] - r * 0.42, centre[1] - 0.20),
                    (centre[0] - r * 0.50, centre[1] + 0.22),
                    (centre[0] + r * 0.50, centre[1] + 0.22),
                    (centre[0] + r * 0.42, centre[1] - 0.20),
                ],
                closed=True, fc=GLASS, alpha=alpha, ec=GLASS, lw=1.2,
            )
        )
    return near, far, r




def problem_3_an_off_centre_push_spins() -> None:
    """Why a push does not go where it was aimed.

    A finger that meets a round glass anywhere but on the line through its
    middle turns it as well as moving it, so the arm has to look again after a
    push rather than assume the glass went where it was sent.
    """
    figure, spin = plt.subplots(figsize=(6.6, 3.6))
    figure.patch.set_facecolor(PAPER)
    spin.set_facecolor(PAPER)

    _bare(spin)
    spin.set_xlim(-0.2, 1.12)
    spin.set_ylim(-0.50, 0.40)
    spin.set_aspect("equal")
    spin.add_patch(Circle((0.55, 0.0), 0.28, fc=GLASS, alpha=0.45, ec=GLASS, lw=1.5))
    spin.plot([0.55], [0.0], marker="+", ms=10, color=INK)
    spin.text(0.55, -0.055, "middle", ha="center", va="top", fontsize=8, color=INK)

    spin.add_patch(
        FancyArrowPatch((0.06, 0.16), (0.27, 0.16), arrowstyle="-|>", mutation_scale=13,
                        color=WARN, lw=1.8)
    )
    spin.text(0.02, 0.26, "a push that misses\nthe middle", fontsize=8.2, color=WARN)
    spin.add_patch(
        FancyArrowPatch((0.72, 0.20), (0.80, -0.05), arrowstyle="-|>", mutation_scale=11,
                        color=WARN, lw=1.4, connectionstyle="arc3,rad=0.5")
    )
    spin.text(0.86, 0.08, "it spins", fontsize=8.4, color=WARN, va="center")

    spin.add_patch(
        FancyArrowPatch((0.06, -0.0), (0.27, -0.0), arrowstyle="-|>", mutation_scale=13,
                        color=GOOD, lw=1.8)
    )
    spin.text(0.02, -0.14, "a push through it", fontsize=8.2, color=GOOD)
    spin.text(0.55, -0.42, "slides roughly straight", ha="center", fontsize=8.4, color=GOOD)

    figure.suptitle(
        "A push that misses the middle turns the glass as well as moving it",
        fontsize=12, color=INK, y=0.97,
    )
    figure.tight_layout()
    _save(figure, "an-off-centre-push-spins.png")


def main() -> None:
    problem_3_the_room_a_gripper_needs()
    problem_3_push_low_or_it_topples()
    problem_3_an_off_centre_push_spins()


if __name__ == "__main__":
    main()
