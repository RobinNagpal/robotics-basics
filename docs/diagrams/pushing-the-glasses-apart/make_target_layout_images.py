"""The picture for the target layout.

The target layout document is the longest in this book and had no picture at
all, so a reader met 3,900 words of geometry as prose. Two things in it are
shape rather than a sentence, and that one is drawn here. Everything else on
that page is a list or an argument, and a picture of a list is padding.

    layout-room-is-asymmetric.png   why a wide glass crowds a narrow one and not the reverse

A picture of all four conditions on one table was drawn and thrown away. The
four conditions are four different things — clear room, inside the zone, within
reach, a clear line of sight — and putting them on one table produced a drawing
in which the rack sat off the paper, the reach ring swamped the glasses, and no
single idea came through. Four conditions are a list, and a list reads better as
a list.

Both are drawn with ``diagram_style``'s own geometry, so the circles, the zone,
the rack and the reach ring are the cell's own numbers rather than numbers
redrawn by eye, and the crowding test is ``has_room``, which is copied from
``bench/bench.py``.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_target_layout_images.py
"""

from __future__ import annotations

import numpy as np
from diagram_style import (
    GOOD,
    GRIP_ROOM,
    INK,
    KIND_NARROWEST,
    KIND_WIDEST,
    MUTED,
    WARN,
    bare,
    glass_from_above,
    grippable,
    new,
    save,
)
from matplotlib.patches import Circle

GLASS = "#3b82c4"




def room_is_asymmetric() -> None:
    """A wide glass and a narrow one at the same distance, and only one is crowded.

    This is the one place a reader can get the geometry backwards, because the
    obvious test — how far apart are the middles — gives the same answer for
    both glasses and the right test does not.
    """
    figure, axis = new(8.8, 4.4)
    bare(axis)
    axis.set_aspect("equal")

    # Between 102.5 mm and 122.5 mm exactly one of the two is crowded, which is
    # the whole point of the picture. Outside that window both answers agree and
    # the picture would show nothing. The window is GRIP_ROOM plus half of each
    # width, so it is the cell's own numbers rather than a chosen gap.
    apart = 112.0
    wide = (0.0, 0.0)
    narrow = (apart, 0.0)

    for centre, rim, colour in ((wide, KIND_WIDEST, GLASS), (narrow, KIND_NARROWEST, GLASS)):
        glass_from_above(axis, centre, rim, colour=colour, alpha=0.30, edge=colour)

    # what each glass needs clear of it: GRIP_ROOM plus half the NEIGHBOUR's width
    narrow_ok = grippable(narrow, wide, width_b=KIND_WIDEST)
    wide_ok = grippable(wide, narrow, width_b=KIND_NARROWEST)

    for centre, needs, ok in ((narrow, GRIP_ROOM + KIND_WIDEST / 2.0, narrow_ok),
                              (wide, GRIP_ROOM + KIND_NARROWEST / 2.0, wide_ok)):
        axis.add_patch(Circle(centre, needs, facecolor="none",
                              edgecolor=GOOD if ok else WARN, lw=1.5,
                              ls=(0, (4, 3)), zorder=4))

    axis.annotate("", xy=narrow, xytext=wide, zorder=6,
                  arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1.2,
                                  shrinkA=0, shrinkB=0))
    # Above the glasses, not on the arrow: at this spacing the two circles leave
    # no clear paper between them.
    axis.text(apart / 2.0, 72, f"{apart:.0f} mm between middles", fontsize=9,
              color=INK, ha="center", va="bottom", zorder=7)

    # One label out to each side, because the two glasses stand 112 mm apart and
    # anything hung underneath them lands on its neighbour's label.
    axis.text(wide[0] - 118, 0, "the wide glass\nhas room",
              fontsize=9.5, color=GOOD, ha="right", va="center",
              weight="bold", zorder=7)
    axis.text(narrow[0] + 160, 0, "the narrow glass\ndoes not",
              fontsize=9.5, color=WARN, ha="left", va="center",
              weight="bold", zorder=7)

    axis.set_xlim(-250, apart + 320)
    axis.set_ylim(-150, 135)
    axis.set_title("The same gap, and only one of the two glasses is crowded",
                   fontsize=12.5, color=INK, pad=12)
    axis.text(0.5, -0.08,
              f"A glass needs {GRIP_ROOM:.0f} mm clear plus half its NEIGHBOUR's width, so the wider "
              "glass is what crowds, and being wide is no disadvantage to itself.",
              transform=axis.transAxes, ha="center", va="top", fontsize=8.5, color=MUTED)

    # The picture claims exactly one of them is crowded. If that stops being
    # true the picture is wrong, so it is checked rather than hoped for.
    if not (wide_ok and not narrow_ok):
        raise SystemExit(
            f"at {apart:.0f} mm the picture's claim is false: "
            f"wide has room = {wide_ok}, narrow has room = {narrow_ok}"
        )
    print(f"  at {apart:.0f} mm apart: wide glass has room = {wide_ok}, "
          f"narrow glass has room = {narrow_ok}  (as the picture claims)")
    save(figure, "layout-room-is-asymmetric.png")


def main() -> None:
    room_is_asymmetric()


if __name__ == "__main__":
    main()
