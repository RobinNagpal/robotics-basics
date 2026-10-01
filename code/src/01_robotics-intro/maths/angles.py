"""Angles and trigonometry, worked out on the two-link arm.

Every number in docs/01_robotics-intro/02_maths/01_angles-and-trigonometry.md
is printed by this file. It covers:

  1. degrees and radians, and how far the tip of a link travels
  2. cos and sin: how far across and how far up a link reaches
  3. atan2: from a point back to its angle, and why plain atan is not enough
  4. the law of cosines: the triangle made by two links
  5. wrapping angles, and what a joint limit does to the shortest turn

The arm is the one the frames doc uses: link 1 is 3 m, link 2 is 2 m, and the
usual pose is q1 = 30 degrees, q2 = 60 degrees.

Run it with:  pixi run python src/maths/angles.py
"""

import math

# The two-link arm from the frames doc: link lengths in metres.
LINK1: float = 3.0
LINK2: float = 2.0


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def wrap_degrees(angle: float) -> float:
    """Bring an angle into the range above -180 and up to 180 degrees."""
    wrapped: float = (angle + 180.0) % 360.0 - 180.0
    # The % above sends +180 to -180. Both point the same way; keep +180.
    return 180.0 if wrapped == -180.0 else wrapped


def degrees_and_radians() -> None:
    """Convert between the two units, and measure the path the tip travels."""
    heading('1. Degrees and radians')

    for degrees in (30.0, 90.0, 180.0, 360.0):
        print(f'{degrees:5.0f} degrees = {math.radians(degrees):.4f} radians')

    # One radian is the angle that moves the tip of a 1 m link 1 m along its arc.
    # So for any link, arc length = link length x angle in radians.
    turn: float = math.radians(30.0)
    print(f'a 1 m link turning 30 degrees: its tip travels {1.0 * turn:.3f} m')
    print(f'a 3 m link turning 30 degrees: its tip travels {LINK1 * turn:.3f} m')

    # The most common bug: passing degrees where radians are expected. No error,
    # just a wrong answer, because 90 is read as 90 radians.
    print(f'math.cos(90) = {math.cos(90):.3f}   but   math.cos(math.radians(90)) = '
          f'{round(math.cos(math.radians(90)), 9) + 0.0:.3f}')


def cos_and_sin() -> None:
    """Turn 'this long, at this angle' into 'this far across, this far up'."""
    heading('2. cos and sin: across and up for a 3 m link')

    print(' angle     cos     sin   across      up')
    for degrees in (0.0, 30.0, 60.0, 90.0, 120.0, 180.0, 270.0):
        a: float = math.radians(degrees)
        # round(... , 9) + 0.0 hides the tiny error in cos(90), which is 6e-17, not 0.
        c: float = round(math.cos(a), 9) + 0.0
        s: float = round(math.sin(a), 9) + 0.0
        print(f'{degrees:6.0f} {c:7.3f} {s:7.3f} {LINK1 * c:8.3f} {LINK1 * s:7.3f}')


def atan2_back() -> None:
    """Find the angle of a point, and show where plain atan goes wrong."""
    heading('3. atan2: from a point back to its angle')

    # The gripper of the usual pose, and the direction from the base to it.
    gx: float = LINK1 * math.cos(math.radians(30)) + LINK2 * math.cos(math.radians(90))
    gy: float = LINK1 * math.sin(math.radians(30)) + LINK2 * math.sin(math.radians(90))
    print(f'gripper at ({gx:.3f}, {gy:.3f})')
    print(f'atan2(y, x) = {math.degrees(math.atan2(gy, gx)):.1f} degrees from the base')

    # Two points in opposite directions. y / x is the same for both, so atan
    # cannot tell them apart. atan2 is given y and x separately, so it can.
    for x, y in ((2.0, 2.0), (-2.0, -2.0), (-2.0, 2.0)):
        plain: float = math.degrees(math.atan(y / x))
        both: float = math.degrees(math.atan2(y, x))
        print(f'point ({x:+.0f}, {y:+.0f})   atan(y/x) = {plain:7.1f}   atan2(y, x) = {both:7.1f}')

    # Straight up, x is 0 and y / x cannot be worked out at all.
    try:
        math.atan(1.0 / 0.0)
    except ZeroDivisionError as error:
        print(f'point (0, +1)   atan(y/x) fails: {error}')
    print(f'point (0, +1)   atan2(y, x) = {math.degrees(math.atan2(1.0, 0.0)):.1f}')


def law_of_cosines() -> None:
    """Relate the elbow angle to the distance from the shoulder to the gripper."""
    heading('4. The law of cosines: the triangle made by two links')

    q2: float = math.radians(60.0)
    # The angle inside the triangle, at the elbow, is 180 degrees minus q2.
    inside: float = math.pi - q2
    d_squared: float = LINK1 ** 2 + LINK2 ** 2 - 2 * LINK1 * LINK2 * math.cos(inside)
    print(f'q2 = 60 degrees, so the angle inside the triangle at the elbow is '
          f'{math.degrees(inside):.0f} degrees')
    print(f'd squared = 9 + 4 - 12 x cos(120) = {d_squared:.3f}')
    print(f'd = {math.sqrt(d_squared):.3f} m from shoulder to gripper')
    print(f'check from the gripper position: sqrt(2.598^2 + 3.5^2) = '
          f'{math.hypot(LINK1 * math.cos(math.radians(30)), 1.5 + 2.0):.3f} m')

    # Backwards: given only the distance, find the elbow angle. This is the
    # first step of inverse kinematics for a two-link arm.
    for d in (math.sqrt(19.0), 5.0, 1.0, 4.0, 6.0):
        cos_q2: float = (d ** 2 - LINK1 ** 2 - LINK2 ** 2) / (2 * LINK1 * LINK2)
        if -1.0 <= cos_q2 <= 1.0:
            print(f'd = {d:.3f} m -> cos(q2) = {cos_q2:+.3f} -> q2 = '
                  f'{math.degrees(math.acos(cos_q2)):.1f} degrees')
        else:
            print(f'd = {d:.3f} m -> cos(q2) = {cos_q2:+.3f} -> no angle has that cosine: '
                  f'out of reach')


def wrapping() -> None:
    """Show that many numbers name one direction, and what a joint limit changes."""
    heading('5. Wrapping angles, and joint limits')

    for angle in (350.0, -10.0, 370.0, 200.0, -190.0, 180.0):
        print(f'{angle:6.0f} degrees wraps to {wrap_degrees(angle):6.0f}')

    # A joint at 170 degrees is told to go to -170 degrees.
    start: float = 170.0
    goal: float = -170.0
    print(f'from {start:.0f} to {goal:.0f}: plain subtraction says turn {goal - start:.0f}')
    print(f'the wrapped difference says turn {wrap_degrees(goal - start):+.0f}')
    # With limits of -175 to +175 degrees, the joint cannot pass through 180.
    limit: float = 175.0
    short_path_end: float = start + wrap_degrees(goal - start)
    print(f'turning +20 would carry the joint to {short_path_end:.0f} degrees, past its '
          f'limit of +{limit:.0f}, so it must turn {goal - start:.0f} instead')


if __name__ == '__main__':
    degrees_and_radians()
    cos_and_sin()
    atan2_back()
    law_of_cosines()
    wrapping()
