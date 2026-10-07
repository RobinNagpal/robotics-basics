"""Two pictures for "how a mask becomes a record".

That page is 1,182 words with no picture at all, and two of its five sections
are geometry: why the axis comes from the top band of the cloud rather than from
all of it, and why the width is a percentile rather than the widest point. Both
are shapes, and a drawing says each in one look. The other three sections are an
argument, a worked consequence and a caveat, and none of them is a shape.

    mask-why-the-axis-is-the-rim.png     the cloud leans; the rim does not
    mask-why-the-width-is-a-percentile.png  one stray point moves the widest
                                            reach and barely moves the 95th

The numbers are the examiner's own: RIM_BAND and SPREAD out of
bench/masks_to_glasses.py, and the splay out of diagram_style's own model of it.

Run from code/:

    pixi run python ../docs/diagrams/seeing-the-glasses/make_mask_to_record_pages.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from diagram_style import GLASS, GOOD, INK, MUTED, NOTE_SIZE, WARN, bare, new, save
from matplotlib.patches import Circle, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                      / "code" / "src" / "08_seeing-the-glasses" / "bench"))

# The examiner's own two settings, from bench/masks_to_glasses.py.
RIM_BAND_MM = 8.0          # masks_to_glasses.RIM_BAND = 0.008
SPREAD = 95                # masks_to_glasses.SPREAD


def why_the_axis_is_the_rim() -> None:
    """A glass seen side on, its leaning cloud, and the two middles.

    One idea: the middle of the whole cloud sits away from the glass and the
    middle of the top band sits over it. Everything else on that page is prose.
    """
    figure, axis = new(8.6, 5.0)
    bare(axis)

    # The glass, side on, with the camera off to one side so the rim leans.
    height, rim, foot = 200.0, 90.0, 48.0
    axis.add_patch(Polygon([(-foot / 2, 0), (foot / 2, 0), (rim / 2, height),
                            (-rim / 2, height)], closed=True,
                           facecolor=GLASS, alpha=0.18, edgecolor=GLASS, lw=1.2))
    axis.plot([-150, 150], [0, 0], color=INK, lw=1.4)
    axis.text(-148, -12, "the table", fontsize=NOTE_SIZE, color=MUTED, va="top")

    # What the camera actually sees of an upright glass standing off to one side
    # of the point below the lens. Back-projection puts every point where it
    # really is, so nothing here is distorted; what is one-sided is which points
    # exist at all. The rim is a ring the camera sees all the way round, so its
    # points ring the axis. Below the rim it sees the wall on one side only,
    # because the glass itself hides the other, and that crescent is what pulls
    # the middle of the whole cloud away from the glass.
    rng = np.random.default_rng(3)
    rim_points = 150
    wall_points = 270

    # the rim: a full ring at the top, seen edge on here, so its two edges
    thetas = rng.uniform(0, 2 * np.pi, rim_points)
    rim_xs = (rim / 2.0) * np.cos(thetas)
    rim_zs = height + rng.normal(0.0, 1.2, rim_points)

    # the wall: one side only, and the camera is to the left, so the far side
    zs_wall = rng.uniform(0.0, height * 0.94, wall_points)
    half_at = (foot + (rim - foot) * zs_wall / height) / 2.0
    wall_xs = half_at * rng.uniform(0.55, 1.0, wall_points)

    xs = np.concatenate([rim_xs, wall_xs])
    zs = np.concatenate([rim_zs, zs_wall])
    axis.plot(xs, zs, ls="none", marker="o", ms=1.9, color=GLASS, alpha=0.6)
    axis.text(-166, height * 0.62, "the camera is off to this side,\nso only the far wall is in\nthe picture",
              fontsize=NOTE_SIZE, color=MUTED, ha="left", va="center")

    whole_middle = float(np.mean(xs))
    band = zs >= zs.max() - RIM_BAND_MM
    rim_middle = float(np.mean(xs[band]))

    # Only as wide as the glass: a band across the whole sheet reads as a rule
    # rather than as the part of the cloud it is.
    axis.axhspan(zs.max() - RIM_BAND_MM, zs.max(), xmin=0.33, xmax=0.67,
                 color=WARN, alpha=0.16, zorder=1)
    axis.plot(xs[band], zs[band], ls="none", marker="o", ms=2.6, color=WARN)
    axis.text(150, zs.max() - RIM_BAND_MM / 2,
              f"the top {RIM_BAND_MM:.0f} mm:\nthe rim", fontsize=NOTE_SIZE,
              color=WARN, va="center", ha="right")

    for x, colour, label, dy in ((whole_middle, MUTED, "the middle of\nthe whole cloud", -18),
                                 (rim_middle, GOOD, "the middle of\nthe rim band", -58)):
        axis.plot([x, x], [-6, height + 14], color=colour, lw=1.3, ls=(0, (4, 3)))
        axis.text(x, dy, label, fontsize=NOTE_SIZE, color=colour, ha="center", va="top")
    axis.plot([0, 0], [-6, height + 14], color=INK, lw=1.2)
    axis.text(0, height + 20, "where the glass really stands",
              fontsize=NOTE_SIZE, color=INK, ha="center", va="bottom")

    # The picture claims the rim band lands nearer the truth than the cloud does.
    if not abs(rim_middle) < abs(whole_middle):
        raise SystemExit(
            f"the picture's claim is false: the rim band is {rim_middle:.1f} mm out "
            f"and the whole cloud {whole_middle:.1f} mm"
        )
    print(f"  whole cloud sits {whole_middle:.0f} mm off, rim band {rim_middle:.0f} mm off")

    axis.set_xlim(-180, 180)
    axis.set_ylim(-96, height + 40)
    axis.set_title("Why the axis comes from the rim and not from the whole cloud",
                   fontsize=12.5, color=INK, pad=10)
    save(figure, "mask-why-the-axis-is-the-rim.png")


def why_the_width_is_a_percentile() -> None:
    """One stray reading, and what it does to each of the two answers."""
    figure, axis = new(8.6, 4.2)
    bare(axis)
    axis.set_aspect("equal")

    rng = np.random.default_rng(11)
    n = 320
    angle = rng.uniform(0, 2 * np.pi, n)
    reach = 45.0 * np.sqrt(rng.uniform(0, 1, n))
    xs, ys = reach * np.cos(angle), reach * np.sin(angle)
    stray = (118.0, 26.0)

    axis.plot(xs, ys, ls="none", marker="o", ms=2.2, color=GLASS, alpha=0.7)
    axis.plot(*stray, marker="o", ms=7, color=WARN, zorder=6)
    axis.text(stray[0] + 9, stray[1], "one stray\ndepth reading", fontsize=NOTE_SIZE,
              color=WARN, va="center", ha="left")

    all_reach = np.append(np.hypot(xs, ys), np.hypot(*stray))
    widest = float(all_reach.max())
    percentile = float(np.percentile(all_reach, SPREAD))

    for radius, colour, label in ((percentile, GOOD, f"the {SPREAD}th percentile: {percentile:.0f} mm"),
                                  (widest, WARN, f"the widest point: {widest:.0f} mm")):
        axis.add_patch(Circle((0, 0), radius, facecolor="none", edgecolor=colour,
                              lw=1.5, ls=(0, (4, 3)), zorder=5))
    axis.plot(0, 0, marker="x", ms=8, mew=1.8, color=INK, zorder=6)

    axis.text(0, -92, f"the {SPREAD}th percentile: {percentile:.0f} mm",
              fontsize=NOTE_SIZE + 0.4, color=GOOD, ha="center", weight="bold")
    axis.text(0, -108, f"the widest point: {widest:.0f} mm",
              fontsize=NOTE_SIZE + 0.4, color=WARN, ha="center", weight="bold")

    if not widest > percentile * 1.5:
        raise SystemExit("the stray point is not stray enough for the picture to make its point")
    print(f"  one stray point: widest {widest:.0f} mm against the {SPREAD}th percentile "
          f"{percentile:.0f} mm")

    axis.set_xlim(-150, 190)
    axis.set_ylim(-125, 95)
    axis.set_title("What one stray reading does to each of the two answers",
                   fontsize=12.5, color=INK, pad=10)
    save(figure, "mask-why-the-width-is-a-percentile.png")


def main() -> None:
    why_the_axis_is_the_rim()
    why_the_width_is_a_percentile()


if __name__ == "__main__":
    main()
