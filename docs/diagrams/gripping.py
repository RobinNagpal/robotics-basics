"""Generate the diagrams used in docs/07_gripping/.

Each picture belongs to one document and illustrates one specific idea from it,
so the images go to docs/images/gripping/<doc-name>/.

Every number drawn here is either a published manufacturer figure or is computed
on the spot from a formula shown in the document, so each picture can be checked
against its source:

  * OnRobot's own datasheets give two payloads per gripper, one for a force fit
    and one for a form fit: RG2 2 kg and 5 kg, 2FG7 7 kg and 11 kg.
  * Robotiq's 2F-85 instruction manual publishes measured grasp forces against
    payloads of six different hardnesses, from 220 N on steel down to 115 N on
    soft rubber.
  * The suction force is p * A, computed here, against OnRobot's published
    6 kg rating for the VGC10 with three 40 mm cups.
  * The friction cone half-angle is arctan(mu), computed here.

Run with:  pixi run python docs/diagrams/gripping.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,  # noqa: E402
                                Polygon, Rectangle, Wedge)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
IMAGES: pathlib.Path = REPO_ROOT / 'docs' / 'images' / 'gripping'

INK: str = '#222222'
MUTED: str = '#777777'
RED: str = '#d1495b'
GREEN: str = '#2a9d3f'
BLUE: str = '#2f6db0'
ORANGE: str = '#f08c1a'
PURPLE: str = '#7b5aa6'
GREY: str = '#9a9a9a'
PALE_BLUE: str = '#e3ecf7'
PALE_GREEN: str = '#dff2e2'
PALE_ORANGE: str = '#fdebd3'
PALE_PURPLE: str = '#ece4f5'
PALE_GREY: str = '#eeeeee'
PALE_RED: str = '#fbe4e8'

ATMOSPHERE_PA: float = 101325.0


def _save(fig: Figure, doc: str, name: str) -> None:
    folder: pathlib.Path = IMAGES / doc
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    plt.close(fig)
    print(f'wrote {folder / name}')


# --------------------------------------------------------------------------
# 01_overview.md
# --------------------------------------------------------------------------

def two_payloads() -> None:
    """One gripper, two payloads, decided by how the fingers ended up.

    The idea is that the headline payload of a gripper is not one number. The
    same motor holding the same object has a different capacity depending on
    whether friction alone is resisting gravity or the finger geometry is doing
    part of the work. OnRobot publish both figures, so no interpretation is
    needed to make the point.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.4))

    grippers = [
        ('OnRobot RG2', 2.0, 5.0),
        ('OnRobot 2FG7', 7.0, 11.0),
    ]

    for ax, (name, force_fit, form_fit) in zip(axes, grippers):
        ax.set_xlim(0, 60)
        ax.set_ylim(-11, 54)
        ax.axis('off')
        ax.text(30, 50.5, name, fontsize=13.0, color=INK, ha='center', weight='bold')

        # ------------------------------------------------ left: a force fit
        # Two flat pads squeezing a block. Nothing but friction holds it.
        ax.text(14, 45.0, 'force fit', fontsize=10.8, color=ORANGE, ha='center')
        ax.text(14, 41.6, 'flat pads, friction only', fontsize=8.8,
                color=MUTED, ha='center')
        for x in (6.0, 20.0):
            ax.add_patch(Rectangle((x, 24), 2.6, 13, facecolor=PALE_GREY,
                                   edgecolor=INK, lw=1.2, zorder=3))
        ax.add_patch(Rectangle((8.6, 25.5), 11.4, 10, facecolor=PALE_ORANGE,
                               edgecolor=ORANGE, lw=1.8, zorder=2))
        for x, d in ((8.0, 1), (20.6, -1)):
            ax.add_patch(FancyArrowPatch((x - 3.2 * d, 30.5), (x, 30.5),
                                         color=ORANGE, lw=1.6, arrowstyle='-|>',
                                         mutation_scale=11, zorder=4))
        ax.add_patch(FancyArrowPatch((14.3, 24.5), (14.3, 18.5), color=MUTED,
                                     lw=1.4, arrowstyle='-|>', mutation_scale=11))
        ax.text(15.6, 20.6, 'it can slide out', fontsize=8.6, color=MUTED)

        # ----------------------------------------------- right: a form fit
        # The fingers are wrapped under the object, so escaping means passing
        # through a finger.
        ax.text(45, 45.0, 'form fit', fontsize=10.8, color=GREEN, ha='center')
        ax.text(45, 41.6, 'fingers wrapped under it', fontsize=8.8,
                color=MUTED, ha='center')
        for x, sign in ((37.0, 1), (51.0, -1)):
            ax.add_patch(Rectangle((x, 24), 2.6, 13, facecolor=PALE_GREY,
                                   edgecolor=INK, lw=1.2, zorder=3))
            # the hook that turns a squeeze into a cradle
            ax.add_patch(Rectangle((x + (2.6 if sign > 0 else -3.4), 24), 3.4, 2.4,
                                   facecolor=PALE_GREY, edgecolor=INK, lw=1.2,
                                   zorder=3))
        ax.add_patch(Rectangle((39.6, 26.4), 11.4, 10, facecolor=PALE_GREEN,
                               edgecolor=GREEN, lw=1.8, zorder=2))
        ax.add_patch(FancyArrowPatch((45.3, 25.4), (45.3, 19.6), color=MUTED,
                                     lw=1.4, arrowstyle='-|>', mutation_scale=11))
        ax.text(46.6, 21.4, 'the finger is in the way', fontsize=8.6, color=MUTED)

        # -------------------------------------------------- the two numbers
        ax.add_patch(FancyBboxPatch((3, 4), 22, 9.5, boxstyle='round,pad=0.6',
                                    facecolor=PALE_ORANGE, edgecolor=ORANGE, lw=1.4))
        ax.text(14, 9.6, f'{force_fit:g} kg', fontsize=17.0, color=INK,
                ha='center', va='center')
        ax.text(14, 5.4, 'published payload', fontsize=8.4, color=MUTED, ha='center')

        ax.add_patch(FancyBboxPatch((34, 4), 22, 9.5, boxstyle='round,pad=0.6',
                                    facecolor=PALE_GREEN, edgecolor=GREEN, lw=1.4))
        ax.text(45, 9.6, f'{form_fit:g} kg', fontsize=17.0, color=INK,
                ha='center', va='center')
        ax.text(45, 5.4, 'published payload', fontsize=8.4, color=MUTED, ha='center')

        factor = form_fit / force_fit
        ax.text(30, -3.0, f'x {factor:.1f}', fontsize=12.0, color=INK, ha='center')
        ax.text(30, -8.0, 'same motor, same object', fontsize=9.0,
                color=MUTED, ha='center')

    fig.text(0.5, -0.02,
             "Both numbers come from the manufacturer's own datasheet for the same product. "
             'Nothing about the gripper changed between them:\nthe capacity is decided by how '
             'the fingers arrived, which on an underactuated gripper is not something you '
             'command.',
             fontsize=10.4, color=INK, ha='center', va='top', linespacing=1.9)

    _save(fig, 'overview', 'two-payloads.svg')


# --------------------------------------------------------------------------
# 02_grippers-and-hardware.md
# --------------------------------------------------------------------------

def force_by_object_hardness() -> None:
    """The grip force you get is a property of the object, not of the gripper.

    Robotiq's 2F-85 manual publishes measured forces against payloads of six
    hardnesses, all with the same fingertip and the same force setting. The
    maximum drops by nearly half as the object gets softer, because a soft
    object gives way and the mechanism runs out of travel before it runs out of
    motor current.
    """
    fig, ax = plt.subplots(figsize=(12.8, 6.2))

    # Robotiq 2F-85 & 2F-140 instruction manual, measured force min/max.
    rows = [
        ('steel 4340\n220 HV', 25, 220, BLUE),
        ('aluminium 6061\n95 HV', 25, 220, BLUE),
        ('silicone\n60 A durometer', 25, 220, BLUE),
        ('silicone rubber\n40 A durometer', 25, 155, ORANGE),
        ('neoprene rubber\n10 A durometer', 25, 115, RED),
        ('polyurethane\n30 OO durometer', 25, 115, RED),
    ]

    y = np.arange(len(rows))[::-1]
    for yi, (_name, lo, hi, colour) in zip(y, rows):
        ax.barh(yi, hi - lo, left=lo, height=0.5, color=colour, alpha=0.85)
        ax.text(hi + 4, yi, f'{hi} N', fontsize=10.4, color=INK, va='center')
        ax.text(lo - 4, yi, f'{lo}', fontsize=9.0, color=MUTED,
                va='center', ha='right')

    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9.4, color=INK,
                       linespacing=1.5)
    ax.set_xlabel('grasp force the Robotiq 2F-85 actually produced, in newtons, '
                  'across its full force setting', fontsize=10.0, color=INK)
    ax.set_xlim(0, 268)
    ax.set_ylim(-1.15, len(rows) - 0.4)
    ax.tick_params(labelsize=9.2, colors=INK)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)

    ax.axvline(235, color=PURPLE, lw=1.4, ls=(0, (5, 4)))
    ax.text(232, -0.98, 'the headline specification: 235 N',
            fontsize=9.4, color=PURPLE, ha='right', va='bottom')

    ax.set_title('One gripper, one setting, six payload materials',
                 fontsize=12.8, color=INK, pad=14)

    fig.text(0.055, -0.06,
             'The gripper did not change and neither did the force setting. What changed is '
             'how much the object gave way.\nA threshold calibrated on a metal part reads a '
             'soft part as never having been gripped at all.',
             fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'grippers-and-hardware', 'force-by-object-hardness.svg')


def suction_arithmetic() -> None:
    """Three numbers for the same suction cup, each smaller than the last.

    Force is pressure difference times area, which is exact arithmetic. Schmalz
    then publish, for the same vacuum level, a cup force about forty per cent
    lower, because the nominal diameter is larger than the area that actually
    seals. OnRobot then rate a payload lower again, because a rating has to
    survive acceleration and a lateral load. Knowing which of the three a number
    is decides whether your gripper works.
    """
    fig, ax = plt.subplots(figsize=(12.8, 6.4))

    # Schmalz flat suction cups SFF, published suction force at -0.6 bar with a
    # smooth dry workpiece and no safety factor applied.
    schmalz = {8: 1.50, 10: 2.70, 15: 5.80, 20: 11.60,
               25: 17.90, 30: 25.10, 40: 47.40, 60: 90.00}
    d_schmalz = np.array(sorted(schmalz), dtype=float)
    f_schmalz = np.array([schmalz[int(d)] for d in d_schmalz]) / 9.81

    d_fine = np.linspace(8, 60, 120)
    ideal = 0.60 * ATMOSPHERE_PA * np.pi * (d_fine / 2000.0) ** 2 / 9.81
    ax.plot(d_fine, ideal, color=PURPLE, lw=2.1,
            label='pressure difference x nominal area, at 60% vacuum')

    ax.plot(d_schmalz, f_schmalz, marker='o', color=BLUE, lw=2.0, markersize=5.5,
            label="Schmalz's published cup force, at the same 60% vacuum")

    ax.plot([40], [2.0], marker='*', markersize=20, color=RED, zorder=5,
            linestyle='none',
            label="OnRobot's rated payload, per 40 mm cup on the VGC10")

    ideal_40 = 0.60 * ATMOSPHERE_PA * np.pi * 0.020 ** 2 / 9.81
    schmalz_40 = schmalz[40] / 9.81

    ax.annotate('', xy=(40, schmalz_40), xytext=(40, ideal_40),
                arrowprops=dict(arrowstyle='<->', color=PURPLE, lw=1.5))
    ax.annotate(f'the area that actually seals is\nsmaller than the cup: '
                f'x {schmalz_40 / ideal_40:.2f}',
                xy=(40.4, (schmalz_40 + ideal_40) / 2), xytext=(18.0, 14.2),
                fontsize=9.6, color=PURPLE, va='center', ha='left',
                linespacing=1.7,
                arrowprops=dict(arrowstyle='-', color=PURPLE, lw=1.0,
                                shrinkA=2, shrinkB=2))

    ax.annotate('', xy=(40, 2.0), xytext=(40, schmalz_40),
                arrowprops=dict(arrowstyle='<->', color=RED, lw=1.5))
    ax.annotate(f'acceleration, lateral load\nand a safety factor: '
                f'x {2.0 / schmalz_40:.2f}',
                xy=(40.4, (2.0 + schmalz_40) / 2), xytext=(48.0, 3.2),
                fontsize=9.6, color=RED, va='center', linespacing=1.7,
                arrowprops=dict(arrowstyle='-', color=RED, lw=1.0,
                                shrinkA=2, shrinkB=2))

    ax.set_xlabel('suction cup diameter, in millimetres', fontsize=10.2, color=INK)
    ax.set_ylabel('force, in kilograms-force', fontsize=10.2, color=INK)
    ax.set_xlim(5, 76)
    ax.set_xticks([10, 20, 30, 40, 50, 60])
    ax.set_ylim(0, 19.5)
    ax.tick_params(labelsize=9.2, colors=INK)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)
    ax.legend(fontsize=9.2, loc='upper left', frameon=False)
    ax.set_title('Three numbers for one 40 mm suction cup, and the gap between them',
                 fontsize=12.8, color=INK, pad=14)

    fig.text(0.055, -0.045,
             f'The line is exact arithmetic. The markers are Schmalz\'s own published forces '
             f'for their flat SFF cups at the same vacuum, and they run\nabout forty per cent '
             f'below it at every size. The star is what OnRobot will actually promise for a '
             f'40 mm cup. From {ideal_40:.1f} kgf to 2.0 kg\nis a factor of '
             f'{ideal_40 / 2.0:.1f}, and it is made of two separate reductions that get '
             f'confused with each other constantly.',
             fontsize=10.4, color=INK, va='top', linespacing=1.9)

    _save(fig, 'grippers-and-hardware', 'suction-arithmetic.svg')


# --------------------------------------------------------------------------
# 03_choosing-a-grip.md
# --------------------------------------------------------------------------

def friction_cone() -> None:
    """Whether the line between two contacts lies inside both friction cones.

    The one test underneath every two-finger grasp. The same object and the
    same gripper give a grasp that holds and a grasp that slides, and which one
    you get is decided by an angle anyone can measure with a protractor.
    """
    mu = 0.3
    half = np.degrees(np.arctan(mu))

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 6.4))

    cases = [
        (0.0, 'squeezed across the diameter', GREEN, PALE_GREEN, 'holds'),
        (30.0, 'squeezed on a chord', RED, PALE_RED, 'slides'),
    ]

    radius = 8.0
    cone_len = 7.4
    centre = np.array([0.0, 3.5])
    for ax, (offset_deg, title, verdict_colour, pale, verdict) in zip(axes, cases):
        ax.set_xlim(-22, 22)
        ax.set_ylim(-21, 18)
        ax.set_aspect('equal')
        ax.axis('off')

        ax.text(0, 16.0, title, fontsize=12.2, color=INK, ha='center', weight='bold')

        # The object: a cylinder seen end-on.
        ax.add_patch(Circle(tuple(centre), radius, facecolor=PALE_GREY,
                            edgecolor=INK, lw=1.7, zorder=3))

        # Two contacts, symmetric about the centre, rotated off the diameter.
        theta = np.radians(offset_deg)
        offsets = [
            np.array([-radius * np.cos(theta), radius * np.sin(theta)]),
            np.array([radius * np.cos(theta), -radius * np.sin(theta)]),
        ]
        contacts = [centre + o for o in offsets]
        # The inward surface normal at each contact points at the centre.
        normals = [-o / np.linalg.norm(o) for o in offsets]

        # The friction cones, drawn over the object so they are visible.
        for c, n in zip(contacts, normals):
            base = np.degrees(np.arctan2(n[1], n[0]))
            ax.add_patch(Wedge(tuple(c), cone_len, base - half, base + half,
                               facecolor=pale, edgecolor=verdict_colour, lw=1.3,
                               alpha=0.92, zorder=5))

        # The squeeze acts along the line joining the contacts.
        line = (contacts[1] - contacts[0]) / np.linalg.norm(contacts[1] - contacts[0])
        for c, d in zip(contacts, (1.0, -1.0)):
            ax.add_patch(FancyArrowPatch(tuple(c + line * d * 9.5), tuple(c),
                                         color=INK, lw=2.4, arrowstyle='-|>',
                                         mutation_scale=16, zorder=7))

        for c in contacts:
            ax.add_patch(Circle(tuple(c), 0.7, facecolor=INK,
                                edgecolor='white', lw=0.8, zorder=8))

        # The normal at the left-hand contact, dashed, with its label outside.
        c, n = contacts[0], normals[0]
        ax.plot([c[0], c[0] + n[0] * cone_len], [c[1], c[1] + n[1] * cone_len],
                color=PURPLE, lw=1.7, ls=(0, (4, 3)), zorder=9)
        ax.annotate('the surface normal', xy=tuple(c + n * cone_len * 0.55),
                    xytext=(-13.0, -4.0), fontsize=9.4, color=PURPLE,
                    ha='center', va='top',
                    arrowprops=dict(arrowstyle='-', color=PURPLE, lw=1.0,
                                    shrinkA=2, shrinkB=2))

        # The angle between them, drawn as an arc with no label of its own.
        if offset_deg > 0:
            base = np.degrees(np.arctan2(n[1], n[0]))
            ax.add_patch(Wedge(tuple(c), 4.6, base, base + offset_deg,
                               facecolor='none', edgecolor=INK, lw=1.5,
                               zorder=9))

        ax.text(2.0, -9.5,
                f'the squeeze sits {offset_deg:.0f} degrees off the normal,\n'
                f'and the cone allows {half:.1f}',
                fontsize=10.2, color=INK, ha='center', va='top', linespacing=1.8)
        ax.text(2.0, -18.2, verdict, fontsize=13.5, color=verdict_colour,
                ha='center', weight='bold')

    fig.text(0.5, 0.02,
             f'The shaded wedge is the friction cone: the set of directions a contact can push '
             f'without slipping. Its half-angle is arctan(mu),\nwhich for mu = {mu} — the value '
             f'Robotiq measured for their silicone fingertip against lubricated steel — is '
             f'{half:.1f} degrees.\nThe right-hand grasp needs 30 degrees, so it fails. On a dry '
             f'part, where mu = 0.6 opens the cone to 31.0 degrees, the same grasp holds.',
             fontsize=10.4, color=INK, ha='center', va='top', linespacing=1.9)

    _save(fig, 'choosing-a-grip', 'friction-cone.svg')


# --------------------------------------------------------------------------
# 05_holding-on.md
# --------------------------------------------------------------------------

def slip_the_gap_cannot_see() -> None:
    """Three ways an object moves in the fingers, and which one the gap reports.

    The finger-position reading is the free slip check every electric gripper
    offers. It is blind to the two failures that matter and sensitive to the one
    nobody was worried about, which is what makes it worse than no check at all.
    """
    from matplotlib.patches import Ellipse

    fig, axes = plt.subplots(1, 3, figsize=(14.6, 6.2))

    radius = 6.0

    panels = [
        ('it slides down out of the grip',
         'the pads stay on the same cross-section\nthe whole way down',
         'the gap does not change', RED),
        ('it rotates between the pads',
         'a round object presents the same width\nat every angle',
         'the gap does not change', RED),
        ('it deforms, and the fingers creep in',
         'the one motion that moves the pads,\nand not the one you feared',
         'the gap changes', GREEN),
    ]

    for i, (ax, (title, why, verdict, colour)) in enumerate(zip(axes, panels)):
        ax.set_xlim(-15, 15)
        ax.set_ylim(-23.4, 17)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.text(0, 15.0, title, fontsize=11.6, color=INK, ha='center', weight='bold')

        squash = 0.74 if i == 2 else 1.0
        half_width = radius * squash

        # The two pads, long enough that a slipping object stays between them.
        for sign in (-1, 1):
            x = sign * (half_width + 0.3) - (1.9 if sign > 0 else 0.0)
            ax.add_patch(Rectangle((x, -11.2), 1.9, 20.7, facecolor=PALE_GREY,
                                   edgecolor=INK, lw=1.3, zorder=4))

        # Where the object has ended up, and its ghost where it started.
        drop = -4.6 if i == 0 else 0.0
        if i == 0:
            ax.add_patch(Circle((0, 0), radius, facecolor='none',
                                edgecolor=GREY, lw=1.1, ls=(0, (4, 3)), zorder=2))
        if i == 2:
            ax.add_patch(Circle((0, 0), radius, facecolor='none',
                                edgecolor=GREY, lw=1.1, ls=(0, (4, 3)), zorder=2))
            ax.add_patch(Ellipse((0, 0), 2 * half_width, 2 * radius * 1.12,
                                 facecolor=PALE_BLUE, edgecolor=BLUE, lw=1.7,
                                 zorder=3))
        else:
            ax.add_patch(Circle((0, drop), radius, facecolor=PALE_BLUE,
                                edgecolor=BLUE, lw=1.7, zorder=3))

        # A painted stripe on the object, so a rotation is visible.
        ang = np.radians(58.0 if i == 1 else 0.0)
        rx = half_width * 0.78
        ry = radius * 0.78
        sx, sy = np.cos(ang) * rx, np.sin(ang) * ry
        ax.plot([-sx, sx], [drop - sy, drop + sy], color=BLUE, lw=2.6, zorder=5)

        # The motion arrow, placed clear of the pads.
        if i == 0:
            ax.add_patch(FancyArrowPatch((10.6, 3.0), (10.6, -5.0), color=MUTED,
                                         lw=1.7, arrowstyle='-|>', mutation_scale=14))
        elif i == 1:
            ax.add_patch(FancyArrowPatch((11.4, -1.5), (11.4, 6.5), color=MUTED,
                                         lw=1.7, arrowstyle='-|>',
                                         mutation_scale=14,
                                         connectionstyle='arc3,rad=-0.55'))
        else:
            for sign in (-1, 1):
                ax.add_patch(FancyArrowPatch((sign * 12.6, 12.2),
                                             (sign * 6.2, 12.2), color=MUTED,
                                             lw=1.7, arrowstyle='-|>',
                                             mutation_scale=14))

        # The measured gap, which is all the gripper actually reports.
        ax.annotate('', xy=(-half_width - 0.3, -13.4),
                    xytext=(half_width + 0.3, -13.4),
                    arrowprops=dict(arrowstyle='<->', color=INK, lw=1.3))
        ax.text(0, -15.8, 'what the gripper reports: the finger gap',
                fontsize=8.8, color=INK, ha='center')
        ax.text(0, -18.4, verdict, fontsize=11.0, color=colour, ha='center')
        ax.text(0, -20.2, why, fontsize=8.6, color=MUTED, ha='center',
                va='top', linespacing=1.6)

    fig.text(0.5, -0.035,
             'The finger-position reading is free, every electric gripper publishes it, and it '
             'is the usual slip check. It is blind to the object\nsliding out and blind to the '
             'object turning, which are the two failures you meant to catch. What it does '
             'detect is the object being\nsquashed. A check on a sensor that cannot observe '
             'the event reports nothing wrong, for ever.',
             fontsize=10.4, color=INK, ha='center', va='top', linespacing=1.9)

    _save(fig, 'holding-on', 'slip-the-gap-cannot-see.svg')


if __name__ == '__main__':
    two_payloads()
    force_by_object_hardness()
    suction_arithmetic()
    friction_cone()
    slip_the_gap_cannot_see()
