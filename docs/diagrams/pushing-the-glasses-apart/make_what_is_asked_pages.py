"""Two pictures for "what is asked for", both of them shapes rather than lists.

That page already carries three drawings of geometry. What it did not carry was
the two things on it that are arguments with a shape: the circle of
dependencies that makes lifting unavailable, and the three ways a run can end.
Everything else on the page is a list of facts, and a picture of a list is
padding.

    asked-the-circle-lifting-cannot-break.png  why the arm drags instead of lifting
    asked-three-ways-a-run-ends.png            done, correct but incomplete, and wrong

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_what_is_asked_pages.py
"""

from __future__ import annotations

import numpy as np
from make_solution_flows_a import (
    GOOD,
    GRIP_ROOM_MM,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    WARN,
    _tint,
    box,
    finish,
    note,
    save,
    sheet,
    title,
)
from matplotlib.patches import FancyArrowPatch

GLASS = "#3b82c4"


def the_circle_lifting_cannot_break() -> None:
    """Four needs in a ring, each one waiting on the next, and the way out.

    Drawn as a ring because it is one: the page states it as four bullet points
    that happen to close on themselves, and a reader who sees the ring sees in
    one look why no amount of effort inside it helps.
    """
    width, height = 9.0, 6.0
    figure, axis = sheet(width, height)

    y = title(figure, axis, width, height - 0.12,
              "Why the arm drags: the circle lifting cannot break") - 0.20

    middle = (width / 2.0, y - 2.35)
    radius = 1.70
    steps = (
        "To lift a glass,\nthe fingers must close\nin a chosen place",
        "To choose that place,\nthe arm needs\nthe glass's profile",
        "To measure the profile,\nit needs a side-on\nphotograph",
        "To take that photograph,\nit needs a viewpoint\nnothing is blocking",
    )
    spots = []
    for k in range(4):
        angle = np.pi / 2.0 - k * np.pi / 2.0
        spots.append((middle[0] + radius * np.cos(angle) * 1.55,
                      middle[1] + radius * np.sin(angle)))

    for spot, text in zip(spots, steps, strict=True):
        box(figure, axis, spot[0], spot[1] + 0.42, 2.9, text,
            edge=WARN, face=_tint(WARN, 0.90), size=NOTE_SIZE)

    # the ring of arrows, each one short of the boxes it joins
    for k in range(4):
        a, b = np.array(spots[k]), np.array(spots[(k + 1) % 4])
        axis.add_patch(FancyArrowPatch(
            tuple(a), tuple(b), arrowstyle="-|>", mutation_scale=11,
            color=WARN, lw=1.3, shrinkA=58, shrinkB=58,
            connectionstyle="arc3,rad=0.16", zorder=5))

    note(axis, middle[0], middle[1] + 0.26,
         "and the crowding\nis what took that\nviewpoint away",
         colour=WARN, size=NOTE_SIZE, ha="center", weight="bold", figure=figure)

    y = min(s[1] for s in spots) - 0.72
    y = box(figure, axis, width / 2.0, y, 6.4,
            "Dragging needs only a contact and a direction, so it starts outside the circle.",
            edge=GOOD, face=_tint(GOOD, 0.84), weight="bold", size=LABEL_SIZE, lw=1.8)
    finish(figure, axis, "asked-the-circle-lifting-cannot-break.png", y - 0.12)
    save(figure, "asked-the-circle-lifting-cannot-break.png")


def three_ways_a_run_ends() -> None:
    """Done, correct but incomplete, and wrong: three endings and no fourth.

    The difference between the second and the third is the whole of this
    project's attitude to doubt, so the two are drawn side by side rather than
    described one after the other.
    """
    width, height = 11.2, 2.4
    figure, axis = sheet(width, height)
    col_w = 3.4
    xs = (0.45 + col_w / 2.0, width / 2.0, width - 0.45 - col_w / 2.0)

    y = title(figure, axis, width, height - 0.12,
              "The three ways a run can end") - 0.30

    endings = (
        ("done",
         f"Every glass has {GRIP_ROOM_MM} mm of clear room\nand a viewpoint, and nothing fell over.",
         GOOD),
        ("correct but incomplete",
         "A glass could not be moved safely,\nand was reported with the reason.",
         MUTED),
        ("wrong",
         "A glass was toppled, or pushed out of\nreach, off the table, or into the rack.",
         WARN),
    )
    bottoms = []
    for x, (heading, body, colour) in zip(xs, endings, strict=True):
        note(axis, x, y, heading, colour=colour, size=LABEL_SIZE + 0.8,
             ha="center", weight="bold", figure=figure)
        bottoms.append(box(figure, axis, x, y - 0.34, col_w, body,
                           edge=colour, face=_tint(colour, 0.90)))

    y = note(axis, width / 2.0, min(bottoms) - 0.28,
             "A refusal is a result. Toppling is the one to watch, because nothing else in this\n"
             "project can recover a glass that has fallen over.",
             colour=INK, size=NOTE_SIZE, ha="center", weight="bold", figure=figure)
    finish(figure, axis, "asked-three-ways-a-run-ends.png", y - 0.10)
    save(figure, "asked-three-ways-a-run-ends.png")


def main() -> None:
    the_circle_lifting_cannot_break()
    three_ways_a_run_ends()


if __name__ == "__main__":
    main()
