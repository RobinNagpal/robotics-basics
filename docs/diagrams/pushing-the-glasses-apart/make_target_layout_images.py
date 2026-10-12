"""The picture for the target layout.

The target layout document is the longest in this book and had no picture at
all, so a reader met 3,900 words of geometry as prose. Two things in it are
shape rather than a sentence, and that one is drawn here. Everything else on
that page is a list or an argument, and a picture of a list is padding.

    layout-room-is-asymmetric.png       why a wide glass crowds a narrow one and not the reverse
    layout-where-a-glass-may-stand.png  the glass zone, the reach ring and the rack, from above
    layout-a-line-of-sight.png          the nine side-on viewpoints round one glass, and which are blocked
    layout-least-movement.png           two legal ways to part a crowded pair, and which one moves less

A picture of all four conditions on one table was drawn and thrown away.
Readers then found the numbers hard to picture one by one, so each condition now
has its own drawing, and the zone, the reach and the rack share one because in
this cell the zone already sits inside the reach and away from the rack. The
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
    COMFORTABLE_REACH,
    GLASS_ZONE,
    GOOD,
    GRIP_ROOM,
    INK,
    KIND_NARROWEST,
    KIND_WIDEST,
    MUTED,
    RACK_AREA,
    ROBOT_BASE,
    WARN,
    bare,
    glass_from_above,
    grippable,
    new,
    save,
)
from matplotlib.patches import Circle, Rectangle, Wedge

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


def where_a_glass_may_stand() -> None:
    """The glass zone, the arm's comfortable reach and the rack, seen from above.

    The point is that one rectangle answers three of the conditions: every
    corner of the zone is inside the reach ring, and the rack is on the far side
    of the arm. Both claims are checked below rather than drawn by eye.
    """
    figure, axis = new(7.6, 7.2)
    bare(axis)
    axis.set_aspect("equal")
    low, high = COMFORTABLE_REACH
    axis.add_patch(Wedge(ROBOT_BASE, high, 0, 360, width=high - low,
                         facecolor=GOOD, alpha=0.10, edgecolor="none", zorder=1))
    for r in (low, high):
        axis.add_patch(Circle(ROBOT_BASE, r, facecolor="none", edgecolor=GOOD,
                              lw=1.0, ls=(0, (4, 3)), zorder=2))
    x0, x1, y0, y1 = GLASS_ZONE
    axis.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=GLASS, alpha=0.18,
                             edgecolor=GLASS, lw=1.6, zorder=3))
    r0, r1, s0, s1 = RACK_AREA
    axis.add_patch(Rectangle((r0, s0), r1 - r0, s1 - s0, facecolor=MUTED, alpha=0.6,
                             edgecolor=INK, lw=1.0, zorder=3))
    axis.add_patch(Circle(ROBOT_BASE, 45, facecolor=INK, zorder=4))
    axis.text(0, -75, "arm base", ha="center", va="top", fontsize=9, color=INK)

    # One glass inside the zone, pushed on out of it.
    start, end = (560.0, -380.0), (700.0, -470.0)
    glass_from_above(axis, start, 90, colour=GLASS, alpha=0.35, edge=GLASS)
    glass_from_above(axis, end, 90, colour=WARN, alpha=0.35, edge=WARN)
    axis.annotate("", xy=end, xytext=start, zorder=6,
                  arrowprops=dict(arrowstyle="-|>", color=WARN, lw=1.4, shrinkA=48, shrinkB=48))
    axis.text(end[0] + 10, end[1] - 60, "pushed out\nof the zone", fontsize=9,
              color=WARN, ha="center", va="top", weight="bold")

    axis.text((x0 + x1) / 2, (y0 + y1) / 2 + 60, "glass zone", ha="center",
              va="center", fontsize=10, color=GLASS, weight="bold")
    axis.text((r0 + r1) / 2, s1 + 25, "rack", ha="center", va="bottom", fontsize=9.5, color=INK)
    axis.text(-high * 0.72, high * 0.72, "the arm's\ncomfortable reach", ha="center",
              va="center", fontsize=9, color=GOOD)

    corners = [(x, y) for x in (x0, x1) for y in (y0, y1)]
    distances = [float(np.hypot(x - ROBOT_BASE[0], y - ROBOT_BASE[1])) for x, y in corners]
    if not (min(distances) >= low and max(distances) <= high):
        raise SystemExit(f"the zone is not inside the reach ring: corners at {distances}")
    if not (s0 > y1):
        raise SystemExit("the rack and the zone share a stretch of table")
    print(f"  zone corners {min(distances):.0f} to {max(distances):.0f} mm from the base, "
          f"inside {low:.0f} to {high:.0f}; rack on the other side  (as the picture claims)")

    axis.set_xlim(-high - 30, high + 30)
    axis.set_ylim(-high - 30, high + 30)
    axis.set_title("The zone is inside the reach, and the rack is elsewhere",
                   fontsize=12.5, color=INK, pad=12)
    save(figure, "layout-where-a-glass-may-stand.png")


def _shares_picture(eye, target, target_width, other, other_width) -> bool:
    """Whether ``other`` overlaps ``target`` in a picture taken from ``eye``.

    The same test as ``_blocked`` in work_cell/task.py: an angle at the camera,
    not a distance from the line of sight.
    """
    to_t = np.subtract(target, eye)
    to_o = np.subtract(other, eye)
    rt, ro = float(np.hypot(*to_t)), float(np.hypot(*to_o))
    turn = to_t[0] * to_o[1] - to_t[1] * to_o[0]
    between = abs(np.arctan2(turn, float(np.dot(to_t, to_o))))
    return between < np.arctan2(target_width / 2, rt) + np.arctan2(other_width / 2, ro)


def a_line_of_sight() -> None:
    """One glass, the nine places the camera may stand to look at it side-on, and
    which of them have another glass in the picture."""
    figure, axis = new(7.6, 7.2)
    bare(axis)
    axis.set_aspect("equal")
    standoff = 380.0
    target, width = (0.0, 0.0), 80.0
    others = [((150.0, 40.0), 90.0), ((-60.0, -150.0), 85.0)]

    glass_from_above(axis, target, width, colour=GLASS, alpha=0.45, edge=GLASS)
    for centre, w in others:
        glass_from_above(axis, centre, w, colour=MUTED, alpha=0.45, edge=MUTED)
    axis.add_patch(Circle(target, standoff, facecolor="none", edgecolor=MUTED,
                          lw=0.8, ls=(0, (2, 3)), zorder=1))
    clear = 0
    for step in range(9):
        angle = np.radians(90 + 40 * step)
        eye = (standoff * np.cos(angle), standoff * np.sin(angle))
        blocked = any(_shares_picture(eye, target, width, c, w) for c, w in others)
        clear += not blocked
        colour = WARN if blocked else GOOD
        # On through the glass and out the far side, because a glass standing
        # behind the one being measured spoils the picture as much as one in front.
        beyond = (-0.75 * eye[0], -0.75 * eye[1])
        style = "-" if not blocked else (0, (3, 2))
        axis.plot([eye[0], target[0]], [eye[1], target[1]], color=colour, lw=1.2,
                  alpha=0.85, zorder=2, ls=style)
        axis.plot([target[0], beyond[0]], [target[1], beyond[1]], color=colour, lw=0.8,
                  alpha=0.3, zorder=2, ls=style)
        axis.add_patch(Circle(eye, 16, facecolor=colour, edgecolor="none", zorder=5))
    axis.text(0, -60, "the glass\nto measure", ha="center", va="top", fontsize=9, color=GLASS)
    axis.text(standoff + 30, -standoff + 40, "green: a clear view\nred: another glass in\nfront, beside or behind",
              fontsize=9, color=INK, ha="right", va="bottom")
    if clear == 0 or clear == 9:
        raise SystemExit(f"{clear} of nine views are clear, so the picture shows nothing")
    print(f"  {clear} of the nine viewpoints are clear  (as the picture shows)")
    axis.set_xlim(-standoff - 60, standoff + 60)
    axis.set_ylim(-standoff - 60, standoff + 60)
    axis.set_title(f"Nine places to look from, {standoff:.0f} mm out; one clear view is enough",
                   fontsize=12, color=INK, pad=12)
    save(figure, "layout-a-line-of-sight.png")


def least_movement() -> None:
    """A crowded pair, and two ways to part it that both end legal.

    Parting both a little and pushing one a long way both satisfy the clear
    room; the layout wants the one with less squared travel, and the numbers
    in the labels are computed here.
    """
    figure, axis = new(8.8, 4.6)
    bare(axis)
    axis.set_aspect("equal")
    width = KIND_NARROWEST
    need = GRIP_ROOM + width / 2.0          # what each needs between middles
    a, b = (0.0, 0.0), (width + 5.0, 0.0)   # 5 mm of daylight: not touching
    gap = need - (b[0] - a[0])              # how much further apart they must be
    both = (a[0] - gap / 2, b[0] + gap / 2)
    one_far = b[0] + 150.0           # a long push to open table
    cost_both = 2 * (gap / 2) ** 2
    cost_far = (one_far - b[0]) ** 2
    if grippable(a, b, width_b=width) or not grippable((both[0], 0), (both[1], 0), width_b=width):
        raise SystemExit("the start is not crowded, or the small move does not part them")

    rows = {"start": 0.0, "both": 150.0, "far": -150.0}
    for x in (a[0], b[0]):
        glass_from_above(axis, (x, rows["start"]), width, colour=MUTED, alpha=0.30, edge=MUTED, foot=False)
    for x in both:
        glass_from_above(axis, (x, rows["both"]), width, colour=GOOD, alpha=0.35, edge=GOOD, foot=False)
    for x in (a[0], one_far):
        glass_from_above(axis, (x, rows["far"]), width, colour=WARN, alpha=0.35, edge=WARN, foot=False)
    # where the moved glasses started, as dashed outlines, so the arrows have a tail
    for x, y in ((a[0], rows["both"]), (b[0], rows["both"]), (b[0], rows["far"])):
        axis.add_patch(Circle((x, y), width / 2, facecolor="none", edgecolor=MUTED,
                              lw=0.9, ls=(0, (3, 2)), zorder=2))
    under = width / 2 + 14
    for sx, ex in ((a[0], both[0]), (b[0], both[1])):
        axis.annotate("", xy=(ex, rows["both"] - under), xytext=(sx, rows["both"] - under),
                      arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=1.4, shrinkA=0, shrinkB=0))
    axis.annotate("", xy=(one_far, rows["far"] - under), xytext=(b[0], rows["far"] - under),
                  arrowprops=dict(arrowstyle="-|>", color=WARN, lw=1.4, shrinkA=0, shrinkB=0))
    left = -110
    axis.text(left, rows["start"], "crowded\nat the start", ha="right", va="center", fontsize=9, color=MUTED)
    axis.text(left, rows["both"], f"each moves {gap / 2:.0f} mm", ha="right", va="center",
              fontsize=9.5, color=GOOD, weight="bold")
    axis.text(left, rows["far"], f"one moves {one_far - b[0]:.0f} mm", ha="right", va="center",
              fontsize=9.5, color=WARN, weight="bold")
    if not cost_both < cost_far:
        raise SystemExit("the long push is not the costlier one")
    print(f"  start {b[0]:.0f} mm apart, need {need:.1f}; squared travel: "
          f"both {cost_both:.0f} mm^2, one far {cost_far:.0f} mm^2")
    axis.set_xlim(-300, one_far + 60)
    axis.set_ylim(-230, 200)
    axis.set_title("Both endings give each glass its room; the layout wants the smaller move",
                   fontsize=12, color=INK, pad=12)
    save(figure, "layout-least-movement.png")


def main() -> None:
    room_is_asymmetric()
    where_a_glass_may_stand()
    a_line_of_sight()
    least_movement()


if __name__ == "__main__":
    main()
