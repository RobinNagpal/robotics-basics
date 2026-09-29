"""Values and lists: how a program holds the numbers that describe an arm.

A robot arm is described by a handful of numbers: how long each link is, and
how far each joint has turned. This file shows the Python that holds them:

  1. variables and the two kinds of number, int and float
  2. degrees and radians, and converting between them
  3. a list of joint angles, and reading one out by its index
  4. a dict of link lengths, looked up by name
  5. f-strings, for printing a position so a person can read it

Run it with:  pixi run python src/python_basics/values_and_lists.py
"""

import math


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def variables() -> None:
    """Give a name to a number, and see what type Python gives it."""
    heading('1. Variables, int and float')

    joint_count: int = 2      # a whole number: an int
    link1_m: float = 3.0      # a number with a decimal point: a float
    print('joint_count =', joint_count, type(joint_count))
    print('link1_m     =', link1_m, type(link1_m))

    # Dividing two ints always gives a float in Python 3.
    print('7 / 2  =', 7 / 2)
    # // throws away the part after the decimal point.
    print('7 // 2 =', 7 // 2)


def degrees_and_radians() -> None:
    """People think in degrees. Python's maths functions want radians."""
    heading('2. Degrees and radians')

    q1_deg: float = 30.0
    q1_rad: float = math.radians(q1_deg)
    print('30 degrees is', q1_rad, 'radians')
    print('back again:  ', math.degrees(q1_rad), 'degrees')

    # The common mistake: passing degrees straight to cos.
    print('math.cos(math.radians(60)) =', math.cos(math.radians(60)))
    print('math.cos(60)               =', math.cos(60))


def lists() -> None:
    """Hold every joint angle of an arm in one list, in order from the base."""
    heading('3. A list of joint angles')

    q: list[float] = [30.0, 60.0]            # degrees, joint 1 first
    print('q          =', q)
    print('len(q)     =', len(q))
    print('q[0]       =', q[0], ' <- joint 1, the one at the base')
    print('q[1]       =', q[1], ' <- joint 2')
    print('q[-1]      =', q[-1], ' <- the last joint, however many there are')

    q[1] = 45.0                              # turn joint 2 to a new angle
    print('after q[1] = 45.0:', q)

    q.append(-60.0)                          # add a third joint
    print('after q.append(-60.0):', q, ' len', len(q))

    # Turn the whole list into radians in one line: a list comprehension.
    q_rad: list[float] = [math.radians(a) for a in q]
    print('in radians:', [round(a, 3) for a in q_rad])


def dicts() -> None:
    """Look link lengths up by name instead of by position."""
    heading('4. A dict of link lengths')

    links_m: dict[str, float] = {'link1': 3.0, 'link2': 2.0}
    print('links_m          =', links_m)
    print("links_m['link2'] =", links_m['link2'])
    print('total reach      =', sum(links_m.values()), 'm')
    for name, length in links_m.items():
        print(f'  {name} is {length} m long')


def f_strings() -> None:
    """Print a position with a fixed number of decimal places."""
    heading('5. f-strings')

    x: float = 3.0 * math.cos(math.radians(30))
    y: float = 3.0 * math.sin(math.radians(30))
    print('plain print:', x, y)
    print(f'f-string:    gripper at ({x:.3f}, {y:.3f}) m')
    print(f'with signs:  gripper at ({x:+.2f}, {y:+.2f}) m')


if __name__ == '__main__':
    variables()
    degrees_and_radians()
    lists()
    dicts()
    f_strings()
